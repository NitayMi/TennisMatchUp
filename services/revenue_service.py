"""
Revenue Service for TennisMatchUp
Centralizes all revenue and financial calculations
"""
from datetime import datetime, timedelta, date
from models.database import db
from models.user import User
from models.player import Player
from models.court import Court, Booking
from sqlalchemy import func, and_, or_
from collections import defaultdict
import calendar


class RevenueService:
    """Centralized revenue and financial analytics service"""
    
    @staticmethod
    def calculate_monthly_revenue(owner_id, month=None, year=None):
        """Calculate revenue for a specific month"""
        try:
            # Default to current month if not specified
            if month is None:
                month = datetime.now().month
            if year is None:
                year = datetime.now().year
            
            # Get first and last day of the month
            first_day = date(year, month, 1)
            if month == 12:
                last_day = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = date(year, month + 1, 1) - timedelta(days=1)
            
            # Calculate revenue from confirmed bookings
            revenue_query = db.session.query(
                func.sum(
                    Court.hourly_rate * 
                    func.extract('hour', Booking.end_time - Booking.start_time)
                ).label('total_revenue')
            ).join(Court).filter(
                Court.owner_id == owner_id,
                Booking.status == 'confirmed',
                Booking.booking_date.between(first_day, last_day)
            ).first()
            
            total_revenue = revenue_query.total_revenue or 0
            
            # Count bookings
            booking_count = db.session.query(Booking).join(Court).filter(
                Court.owner_id == owner_id,
                Booking.status == 'confirmed',
                Booking.booking_date.between(first_day, last_day)
            ).count()
            
            return {
                'success': True,
                'month': month,
                'year': year,
                'month_name': calendar.month_name[month],
                'total_revenue': float(total_revenue),
                'formatted_revenue': f"${total_revenue:.2f}",
                'booking_count': booking_count,
                'average_booking_value': float(total_revenue / booking_count) if booking_count > 0 else 0,
                'period': {
                    'start_date': first_day.isoformat(),
                    'end_date': last_day.isoformat()
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Revenue calculation failed: {str(e)}'}
    
    @staticmethod
    def get_revenue_analytics(owner_id, period_days=90):
        """Get comprehensive revenue analytics"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=period_days)
            
            # Get all confirmed bookings in period
            bookings = db.session.query(Booking).join(Court).filter(
                Court.owner_id == owner_id,
                Booking.status == 'confirmed',
                Booking.booking_date.between(start_date, end_date)
            ).all()
            
            # Calculate basic metrics
            total_revenue = sum(b.total_cost or b.calculate_cost() for b in bookings)
            total_bookings = len(bookings)
            avg_booking_value = total_revenue / total_bookings if total_bookings > 0 else 0
            
            # Revenue by court
            court_revenue = defaultdict(float)
            court_bookings = defaultdict(int)
            for booking in bookings:
                court_key = booking.court.name
                court_revenue[court_key] += booking.total_cost or booking.calculate_cost()
                court_bookings[court_key] += 1
            
            # Revenue by day of week
            weekday_revenue = defaultdict(float)
            weekday_bookings = defaultdict(int)
            for booking in bookings:
                day_name = booking.booking_date.strftime('%A')
                weekday_revenue[day_name] += booking.total_cost or booking.calculate_cost()
                weekday_bookings[day_name] += 1
            
            # Revenue by hour
            hourly_revenue = defaultdict(float)
            hourly_bookings = defaultdict(int)
            for booking in bookings:
                hour = booking.start_time.hour
                hourly_revenue[hour] += booking.total_cost or booking.calculate_cost()
                hourly_bookings[hour] += 1
            
            # Monthly trends (if period is long enough)
            monthly_trends = {}
            if period_days >= 30:
                monthly_data = defaultdict(float)
                for booking in bookings:
                    month_key = booking.booking_date.strftime('%Y-%m')
                    monthly_data[month_key] += booking.total_cost or booking.calculate_cost()
                monthly_trends = dict(sorted(monthly_data.items()))
            
            # Top performing courts
            top_courts = sorted(
                [(court, revenue) for court, revenue in court_revenue.items()],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            # Peak hours
            peak_hours = sorted(
                [(hour, revenue) for hour, revenue in hourly_revenue.items()],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            return {
                'success': True,
                'period_days': period_days,
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'summary': {
                    'total_revenue': float(total_revenue),
                    'formatted_total_revenue': f"${total_revenue:.2f}",
                    'total_bookings': total_bookings,
                    'average_booking_value': float(avg_booking_value),
                    'formatted_avg_value': f"${avg_booking_value:.2f}",
                    'daily_average': float(total_revenue / period_days),
                    'formatted_daily_avg': f"${total_revenue / period_days:.2f}"
                },
                'breakdown': {
                    'by_court': dict(court_revenue),
                    'by_weekday': dict(weekday_revenue),
                    'by_hour': dict(hourly_revenue)
                },
                'trends': {
                    'monthly': monthly_trends
                },
                'top_performers': {
                    'courts': [{'name': court, 'revenue': float(revenue), 'bookings': court_bookings[court]} 
                              for court, revenue in top_courts],
                    'peak_hours': [{'hour': hour, 'revenue': float(revenue), 'formatted_hour': f"{hour:02d}:00"} 
                                  for hour, revenue in peak_hours]
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Analytics calculation failed: {str(e)}'}
    
    @staticmethod
    def generate_financial_report(owner_id, start_date, end_date):
        """Generate comprehensive financial report"""
        try:
            # Convert string dates if needed
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # Get all bookings in period (all statuses)
            all_bookings = db.session.query(Booking).join(Court).filter(
                Court.owner_id == owner_id,
                Booking.booking_date.between(start_date, end_date)
            ).all()
            
            # Categorize bookings by status
            confirmed_bookings = [b for b in all_bookings if b.status == 'confirmed']
            pending_bookings = [b for b in all_bookings if b.status == 'pending']
            cancelled_bookings = [b for b in all_bookings if b.status == 'cancelled']
            rejected_bookings = [b for b in all_bookings if b.status == 'rejected']
            
            # Calculate revenues
            confirmed_revenue = sum(b.total_cost or b.calculate_cost() for b in confirmed_bookings)
            potential_revenue = sum(b.total_cost or b.calculate_cost() for b in pending_bookings)
            lost_revenue = sum(b.total_cost or b.calculate_cost() for b in cancelled_bookings + rejected_bookings)
            
            # Calculate metrics
            total_requests = len(all_bookings)
            approval_rate = (len(confirmed_bookings) / total_requests * 100) if total_requests > 0 else 0
            cancellation_rate = (len(cancelled_bookings) / total_requests * 100) if total_requests > 0 else 0
            
            # Court performance
            court_performance = {}
            owner_courts = Court.query.filter_by(owner_id=owner_id).all()
            
            for court in owner_courts:
                court_bookings = [b for b in all_bookings if b.court_id == court.id]
                court_confirmed = [b for b in court_bookings if b.status == 'confirmed']
                court_revenue = sum(b.total_cost or b.calculate_cost() for b in court_confirmed)
                
                # Calculate utilization (simplified: bookings per week)
                weeks_in_period = max(1, (end_date - start_date).days / 7)
                utilization_rate = len(court_confirmed) / weeks_in_period
                
                court_performance[court.name] = {
                    'total_bookings': len(court_bookings),
                    'confirmed_bookings': len(court_confirmed),
                    'revenue': float(court_revenue),
                    'formatted_revenue': f"${court_revenue:.2f}",
                    'utilization_rate': float(utilization_rate),
                    'approval_rate': (len(court_confirmed) / len(court_bookings) * 100) if court_bookings else 0
                }
            
            # Weekly breakdown
            weekly_data = defaultdict(lambda: {'bookings': 0, 'revenue': 0.0})
            for booking in confirmed_bookings:
                week_start = booking.booking_date - timedelta(days=booking.booking_date.weekday())
                week_key = week_start.strftime('%Y-%m-%d')
                weekly_data[week_key]['bookings'] += 1
                weekly_data[week_key]['revenue'] += booking.total_cost or booking.calculate_cost()
            
            return {
                'success': True,
                'report_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': (end_date - start_date).days + 1
                },
                'financial_summary': {
                    'confirmed_revenue': float(confirmed_revenue),
                    'formatted_confirmed': f"${confirmed_revenue:.2f}",
                    'potential_revenue': float(potential_revenue),
                    'formatted_potential': f"${potential_revenue:.2f}",
                    'lost_revenue': float(lost_revenue),
                    'formatted_lost': f"${lost_revenue:.2f}",
                    'total_possible': float(confirmed_revenue + potential_revenue + lost_revenue),
                    'formatted_total_possible': f"${confirmed_revenue + potential_revenue + lost_revenue:.2f}"
                },
                'booking_statistics': {
                    'total_requests': total_requests,
                    'confirmed': len(confirmed_bookings),
                    'pending': len(pending_bookings),
                    'cancelled': len(cancelled_bookings),
                    'rejected': len(rejected_bookings),
                    'approval_rate': float(approval_rate),
                    'cancellation_rate': float(cancellation_rate)
                },
                'court_performance': court_performance,
                'weekly_breakdown': dict(weekly_data),
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Report generation failed: {str(e)}'}
    
    @staticmethod
    def calculate_owner_dashboard_stats(owner_id):
        """Calculate key stats for owner dashboard"""
        try:
            # Get owner's courts
            courts = Court.query.filter_by(owner_id=owner_id).all()
            total_courts = len(courts)
            active_courts = len([c for c in courts if c.is_active])
            
            # Current month revenue
            current_month_result = RevenueService.calculate_monthly_revenue(owner_id)
            monthly_revenue = current_month_result.get('total_revenue', 0) if current_month_result['success'] else 0
            
            # Last 7 days activity
            week_ago = datetime.now() - timedelta(days=7)
            recent_bookings = db.session.query(Booking).join(Court).filter(
                Court.owner_id == owner_id,
                Booking.created_at >= week_ago
            ).order_by(Booking.created_at.desc()).limit(10).all()
            
            # Pending bookings count
            pending_bookings = db.session.query(Booking).join(Court).filter(
                Court.owner_id == owner_id,
                Booking.status == 'pending'
            ).count()
            
            # Unread messages count (from models.message import Message would be needed)
            try:
                from models.message import Message
                unread_messages = Message.query.filter_by(
                    receiver_id=owner_id,
                    is_read=False
                ).count()
            except ImportError:
                unread_messages = 0
            
            # Format recent bookings for display
            formatted_bookings = []
            for booking in recent_bookings:
                formatted_bookings.append({
                    'id': booking.id,
                    'player_name': booking.player.user.full_name,
                    'court_name': booking.court.name,
                    'booking_date': booking.booking_date.strftime('%B %d'),
                    'time_range': f"{booking.start_time.strftime('%H:%M')} - {booking.end_time.strftime('%H:%M')}",
                    'status': booking.status,
                    'status_color': booking.get_status_color(),
                    'total_cost': booking.total_cost or booking.calculate_cost(),
                    'created_at': booking.created_at.strftime('%B %d at %H:%M')
                })
            
            return {
                'success': True,
                'stats': {
                    'total_courts': total_courts,
                    'active_courts': active_courts,
                    'pending_bookings': pending_bookings,
                    'monthly_revenue': float(monthly_revenue),
                    'formatted_monthly_revenue': f"${monthly_revenue:.0f}",
                    'unread_messages': unread_messages
                },
                'recent_bookings': formatted_bookings,
                'courts': [{'id': c.id, 'name': c.name, 'is_active': c.is_active} for c in courts]
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Dashboard stats calculation failed: {str(e)}'}
    
    @staticmethod
    def get_revenue_comparison(owner_id, compare_periods=True):
        """Compare revenue across different periods"""
        try:
            current_month = datetime.now()
            last_month = (current_month.replace(day=1) - timedelta(days=1))
            
            # Current month revenue
            current_result = RevenueService.calculate_monthly_revenue(
                owner_id, current_month.month, current_month.year
            )
            
            # Previous month revenue
            previous_result = RevenueService.calculate_monthly_revenue(
                owner_id, last_month.month, last_month.year
            )
            
            if not current_result['success'] or not previous_result['success']:
                return {'success': False, 'error': 'Failed to calculate comparison data'}
            
            current_revenue = current_result['total_revenue']
            previous_revenue = previous_result['total_revenue']
            
            # Calculate percentage change
            if previous_revenue > 0:
                percentage_change = ((current_revenue - previous_revenue) / previous_revenue) * 100
            else:
                percentage_change = 100 if current_revenue > 0 else 0
            
            # Determine trend
            if percentage_change > 10:
                trend = 'strong_growth'
                trend_icon = '📈'
                trend_color = 'success'
            elif percentage_change > 0:
                trend = 'growth'
                trend_icon = '📊'
                trend_color = 'success'
            elif percentage_change > -10:
                trend = 'stable'
                trend_icon = '📊'
                trend_color = 'warning'
            else:
                trend = 'decline'
                trend_icon = '📉'
                trend_color = 'danger'
            
            return {
                'success': True,
                'comparison': {
                    'current_month': {
                        'revenue': float(current_revenue),
                        'formatted': f"${current_revenue:.2f}",
                        'bookings': current_result['booking_count'],
                        'month_name': current_result['month_name']
                    },
                    'previous_month': {
                        'revenue': float(previous_revenue),
                        'formatted': f"${previous_revenue:.2f}",
                        'bookings': previous_result['booking_count'],
                        'month_name': previous_result['month_name']
                    },
                    'change': {
                        'amount': float(current_revenue - previous_revenue),
                        'formatted_amount': f"${current_revenue - previous_revenue:+.2f}",
                        'percentage': float(percentage_change),
                        'formatted_percentage': f"{percentage_change:+.1f}%",
                        'trend': trend,
                        'trend_icon': trend_icon,
                        'trend_color': trend_color
                    }
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Revenue comparison failed: {str(e)}'}
    
    @staticmethod
    def predict_monthly_revenue(owner_id):
        """Predict end-of-month revenue based on current trends"""
        try:
            current_date = datetime.now().date()
            month_start = current_date.replace(day=1)
            days_elapsed = (current_date - month_start).days + 1
            
            # Get revenue so far this month
            current_month_result = RevenueService.calculate_monthly_revenue(owner_id)
            if not current_month_result['success']:
                return {'success': False, 'error': 'Failed to get current revenue data'}
            
            current_revenue = current_month_result['total_revenue']
            
            # Calculate days in current month
            if current_date.month == 12:
                next_month = current_date.replace(year=current_date.year + 1, month=1, day=1)
            else:
                next_month = current_date.replace(month=current_date.month + 1, day=1)
            
            days_in_month = (next_month - month_start).days
            
            # Simple linear prediction
            if days_elapsed > 0:
                daily_average = current_revenue / days_elapsed
                predicted_monthly_revenue = daily_average * days_in_month
            else:
                predicted_monthly_revenue = 0
            
            # Get last month for comparison
            last_month_result = RevenueService.calculate_monthly_revenue(
                owner_id, 
                current_date.month - 1 if current_date.month > 1 else 12,
                current_date.year if current_date.month > 1 else current_date.year - 1
            )
            
            last_month_revenue = last_month_result.get('total_revenue', 0) if last_month_result['success'] else 0
            
            return {
                'success': True,
                'prediction': {
                    'current_revenue': float(current_revenue),
                    'formatted_current': f"${current_revenue:.2f}",
                    'predicted_monthly': float(predicted_monthly_revenue),
                    'formatted_predicted': f"${predicted_monthly_revenue:.2f}",
                    'remaining_predicted': float(predicted_monthly_revenue - current_revenue),
                    'formatted_remaining': f"${predicted_monthly_revenue - current_revenue:.2f}",
                    'days_elapsed': days_elapsed,
                    'days_remaining': days_in_month - days_elapsed,
                    'daily_average': float(daily_average) if days_elapsed > 0 else 0,
                    'formatted_daily_avg': f"${daily_average:.2f}" if days_elapsed > 0 else "$0.00",
                    'vs_last_month': {
                        'amount': float(predicted_monthly_revenue - last_month_revenue),
                        'percentage': float((predicted_monthly_revenue - last_month_revenue) / last_month_revenue * 100) if last_month_revenue > 0 else 0
                    }
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Revenue prediction failed: {str(e)}'}