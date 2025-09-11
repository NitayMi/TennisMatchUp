"""
TennisMatchUp Dashboard Service
Centralized dashboard data processing to maintain MVC separation
"""

from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import joinedload
from models.database import db
from models.user import User
from models.player import Player
from models.court import Court, Booking
from models.shared_booking import SharedBooking
from services.report_service import ReportService
from services.court_recommendation_engine import CourtRecommendationEngine
from utils.db_helpers import db_retry, safe_db_operation
import json


class DashboardService:
    """Centralized service for dashboard data processing"""
    
    @staticmethod
    @db_retry(max_retries=3)
    def get_player_dashboard_data(player_id):
        """
        Get comprehensive dashboard data for a player
        Extracted from routes/player.py to maintain MVC separation
        """
        try:
            player = Player.query.get(player_id)
            if not player:
                return {
                    'success': False, 
                    'error': 'Player not found',
                    'stats': {'total_bookings': 0, 'confirmed_bookings': 0, 'pending_bookings': 0},
                    'upcoming_bookings': [],
                    'recommended_courts': [],
                    'recent_invites': []
                }
            
            # Get upcoming bookings with court details (all active statuses)
            upcoming_bookings = Booking.query.join(Court).filter(
                Booking.player_id == player_id,
                Booking.status.in_(['confirmed', 'pending']),  # Include both confirmed and pending
                Booking.booking_date >= datetime.now().date()
            ).order_by(Booking.booking_date.asc(), Booking.start_time.asc()).limit(5).all()
            
            # Also get upcoming shared bookings (explicit join on main court_id)
            upcoming_shared = SharedBooking.query.join(Court, SharedBooking.court_id == Court.id).filter(
                or_(
                    SharedBooking.player1_id == player_id,
                    SharedBooking.player2_id == player_id
                ),
                SharedBooking.status.in_(['confirmed', 'accepted']),  # Include confirmed and accepted shared bookings
                SharedBooking.booking_date >= datetime.now().date()
            ).order_by(SharedBooking.booking_date.asc(), SharedBooking.start_time.asc()).limit(5).all()
            
            # Combine and sort all upcoming bookings
            all_upcoming = list(upcoming_bookings) + list(upcoming_shared)
            all_upcoming.sort(key=lambda x: (x.booking_date, x.start_time))
            all_upcoming = all_upcoming[:5]  # Limit to 5 total
            
            # Get court recommendations
            court_results = CourtRecommendationEngine.find_recommended_courts(
                player_id=player.id,
                limit=6
            )
            
            # Format court results
            courts_metadata = []
            for result in court_results:
                court_data = {
                    'court': result['court'],
                    'total_score': result['total_score'],
                    'distance_km': result.get('distance_km', 0),
                    'compatibility_score': result.get('compatibility_score', 0),
                    'price_score': result.get('price_score', 0)
                }
                courts_metadata.append(court_data)
            
            # Get recent shared booking invites
            recent_invites = SharedBooking.query.filter(
                or_(
                    SharedBooking.player1_id == player_id,
                    SharedBooking.player2_id == player_id
                )
            ).order_by(SharedBooking.proposed_at.desc()).limit(3).all()
            
            # Get comprehensive statistics including shared bookings
            regular_total = Booking.query.filter_by(player_id=player_id).count()
            shared_total = SharedBooking.query.filter(
                or_(
                    SharedBooking.player1_id == player_id,
                    SharedBooking.player2_id == player_id
                )
            ).count()
            
            stats = {
                'total_bookings': regular_total + shared_total,
                'confirmed_bookings': Booking.query.filter_by(
                    player_id=player_id, 
                    status='confirmed'
                ).count() + SharedBooking.query.filter(
                    or_(
                        SharedBooking.player1_id == player_id,
                        SharedBooking.player2_id == player_id
                    ),
                    SharedBooking.status.in_(['confirmed', 'accepted'])
                ).count(),
                'pending_bookings': Booking.query.filter_by(
                    player_id=player_id, 
                    status='pending'
                ).count() + SharedBooking.query.filter(
                    or_(
                        SharedBooking.player1_id == player_id,
                        SharedBooking.player2_id == player_id
                    ),
                    SharedBooking.status.in_(['proposed', 'counter_proposed'])
                ).count()
            }
            
            return {
                'success': True,
                'upcoming_bookings': all_upcoming,
                'recommended_courts': courts_metadata,
                'recent_invites': recent_invites,
                'stats': stats
            }
            
        except Exception as e:
            print(f"Dashboard service error: {e}")
            # Return safe fallback data on database errors
            return {
                'success': False, 
                'error': f'Database connection error: {str(e)}',
                'stats': {'total_bookings': 0, 'confirmed_bookings': 0, 'pending_bookings': 0},
                'upcoming_bookings': [],
                'recommended_courts': [],
                'recent_invites': []
            }
    
    @staticmethod
    def get_unified_calendar_data(player_id):
        """
        Get unified calendar data for player calendar view
        Extracted from routes/player.py my-calendar route (70+ lines)
        """
        try:
            # Get regular bookings
            regular_bookings = Booking.query.join(Court).options(
                joinedload(Booking.court)
            ).filter(
                Booking.player_id == player_id
            ).all()
            
            # Get shared bookings where player is involved
            shared_bookings = SharedBooking.query.filter(
                or_(
                    SharedBooking.player1_id == player_id,
                    SharedBooking.player2_id == player_id
                )
            ).options(
                joinedload(SharedBooking.court),
                joinedload(SharedBooking.player1).joinedload(Player.user),
                joinedload(SharedBooking.player2).joinedload(Player.user)
            ).all()
            
            # Return both raw bookings for template and formatted data for calendar
            # Raw bookings for template (needs actual booking objects)
            all_booking_objects = list(regular_bookings) + list(shared_bookings)
            
            # Process unified booking data for calendar JSON
            all_bookings_data = []
            
            # Process regular bookings
            for booking in regular_bookings:
                booking_data = {
                    'id': booking.id,
                    'type': 'regular',
                    'title': f"{booking.court.name}",
                    'start': f"{booking.booking_date}T{booking.start_time}",
                    'end': f"{booking.booking_date}T{booking.end_time}",
                    'booking_date': str(booking.booking_date),
                    'start_time': str(booking.start_time),
                    'end_time': str(booking.end_time),
                    'status': booking.status,
                    'court_name': booking.court.name,
                    'court_location': booking.court.location,
                    'court': {
                        'id': booking.court.id,
                        'name': booking.court.name,
                        'location': booking.court.location
                    },
                    'total_cost': float(booking.total_cost) if booking.total_cost else 0,
                    'notes': booking.notes or '',
                    'backgroundColor': DashboardService._get_booking_color(booking.status),
                    'borderColor': DashboardService._get_booking_color(booking.status),
                    'textColor': '#ffffff'
                }
                all_bookings_data.append(booking_data)
            
            # Process shared bookings
            for shared_booking in shared_bookings:
                # Determine partner
                partner = (shared_booking.player2 if shared_booking.player1_id == player_id 
                          else shared_booking.player1)
                
                booking_data = {
                    'id': f"shared_{shared_booking.id}",
                    'type': 'shared',
                    'title': f"{shared_booking.court.name} with {partner.user.full_name}",
                    'start': f"{shared_booking.booking_date}T{shared_booking.start_time}",
                    'end': f"{shared_booking.booking_date}T{shared_booking.end_time}",
                    'booking_date': str(shared_booking.booking_date),
                    'start_time': str(shared_booking.start_time),
                    'end_time': str(shared_booking.end_time),
                    'status': shared_booking.status,
                    'court_name': shared_booking.court.name,
                    'court_location': shared_booking.court.location,
                    'court': {
                        'id': shared_booking.court.id,
                        'name': shared_booking.court.name,
                        'location': shared_booking.court.location
                    },
                    'partner': partner.user.full_name,
                    'partner_name': partner.user.full_name,
                    'total_cost': float(shared_booking.total_cost) if shared_booking.total_cost else 0,
                    'notes': shared_booking.initiator_notes or '',
                    'backgroundColor': DashboardService._get_shared_booking_color(shared_booking.status),
                    'borderColor': DashboardService._get_shared_booking_color(shared_booking.status),
                    'textColor': '#ffffff'
                }
                all_bookings_data.append(booking_data)
            
            return {
                'success': True,
                'booking_objects': all_booking_objects,  # Raw booking objects for template
                'bookings': all_bookings_data,           # Formatted data for calendar
                'bookings_json': json.dumps(all_bookings_data)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_owner_dashboard_stats(owner_id):
        """Get dashboard statistics for court owners"""
        try:
            # Get owner's courts
            owner_courts = Court.query.filter_by(owner_id=owner_id, is_active=True).all()
            court_ids = [court.id for court in owner_courts]
            
            if not court_ids:
                return {
                    'success': True,
                    'stats': {
                        'total_courts': 0,
                        'total_bookings': 0,
                        'pending_requests': 0,
                        'monthly_revenue': 0,
                        'recent_bookings': []
                    }
                }
            
            # Calculate statistics
            total_bookings = Booking.query.filter(Booking.court_id.in_(court_ids)).count()
            pending_requests = Booking.query.filter(
                Booking.court_id.in_(court_ids),
                Booking.status == 'pending'
            ).count()
            
            # Monthly revenue
            current_month = datetime.now().replace(day=1)
            monthly_bookings = Booking.query.filter(
                Booking.court_id.in_(court_ids),
                Booking.status == 'confirmed',
                Booking.booking_date >= current_month.date()
            ).all()
            
            monthly_revenue = sum(booking.total_cost for booking in monthly_bookings 
                                if booking.total_cost)
            
            # Recent bookings
            recent_bookings = Booking.query.join(Court).filter(
                Booking.court_id.in_(court_ids)
            ).order_by(Booking.created_at.desc()).limit(10).all()
            
            return {
                'success': True,
                'stats': {
                    'total_courts': len(owner_courts),
                    'total_bookings': total_bookings,
                    'pending_requests': pending_requests,
                    'monthly_revenue': monthly_revenue,
                    'recent_bookings': recent_bookings
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _get_booking_color(status):
        """Get color code for booking status"""
        color_map = {
            'confirmed': '#28a745',
            'pending': '#ffc107',
            'cancelled': '#dc3545',
            'rejected': '#6c757d'
        }
        return color_map.get(status, '#6c757d')
    
    @staticmethod
    def _get_shared_booking_color(status):
        """Get color code for shared booking status"""
        color_map = {
            'confirmed': '#17a2b8',
            'pending': '#fd7e14',
            'cancelled': '#dc3545',
            'rejected': '#6c757d'
        }
        return color_map.get(status, '#6c757d')