"""
Report Service for TennisMatchUp
Centralizes all reporting and analytics generation
"""
from datetime import datetime, timedelta, date
from models.database import db
from models.user import User
from models.player import Player
from models.court import Court, Booking
from models.message import Message
from sqlalchemy import func, and_, or_, desc
from collections import defaultdict
import json


class ReportService:
    """Centralized reporting and analytics service"""
    
    @staticmethod
    def generate_admin_dashboard_stats():
        """Generate comprehensive admin dashboard statistics"""
        try:
            # User statistics
            total_users = User.query.count()
            total_players = Player.query.count()
            total_owners = User.query.filter_by(user_type='owner').count()
            active_users = User.query.filter_by(is_active=True).count()
            
            # Recent registrations (last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            recent_users = User.query.filter(User.created_at >= week_ago).count()
            
            # Court statistics
            total_courts = Court.query.count()
            active_courts = Court.query.filter_by(is_active=True).count()
            
            # Booking statistics
            total_bookings = Booking.query.count()
            confirmed_bookings = Booking.query.filter_by(status='confirmed').count()
            pending_bookings = Booking.query.filter_by(status='pending').count()
            cancelled_bookings = Booking.query.filter_by(status='cancelled').count()
            rejected_bookings = Booking.query.filter_by(status='rejected').count()
            
            # Revenue statistics (last 30 days)
            month_ago = datetime.now() - timedelta(days=30)
            monthly_revenue = db.session.query(
                func.sum(Court.hourly_rate * 
                        func.extract('hour', Booking.end_time - Booking.start_time))
            ).join(Booking).filter(
                Booking.status == 'confirmed',
                Booking.booking_date >= month_ago.date()
            ).scalar() or 0
            
            # Today's bookings
            today_bookings = Booking.query.filter_by(
                booking_date=datetime.now().date()
            ).count()
            
            # System health metrics
            avg_approval_rate = (confirmed_bookings / total_bookings * 100) if total_bookings > 0 else 0
            cancellation_rate = (cancelled_bookings / total_bookings * 100) if total_bookings > 0 else 0
            
            return {
                'success': True,
                'stats': {
                    'users': {
                        'total': total_users,
                        'players': total_players,
                        'owners': total_owners,
                        'active': active_users,
                        'recent': recent_users,
                        'inactive': total_users - active_users
                    },
                    'courts': {
                        'total': total_courts,
                        'active': active_courts,
                        'inactive': total_courts - active_courts
                    },
                    'bookings': {
                        'total': total_bookings,
                        'confirmed': confirmed_bookings,
                        'pending': pending_bookings,
                        'cancelled': cancelled_bookings,
                        'rejected': rejected_bookings,
                        'today': today_bookings
                    },
                    'revenue': {
                        'monthly': float(monthly_revenue),
                        'formatted_monthly': f"${monthly_revenue:.2f}",
                        'daily_average': float(monthly_revenue / 30),
                        'formatted_daily_avg': f"${monthly_revenue / 30:.2f}"
                    },
                    'health': {
                        'approval_rate': float(avg_approval_rate),
                        'cancellation_rate': float(cancellation_rate),
                        'formatted_approval': f"{avg_approval_rate:.1f}%",
                        'formatted_cancellation': f"{cancellation_rate:.1f}%"
                    }
                },
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Dashboard stats generation failed: {str(e)}'}
    
    @staticmethod
    def create_user_activity_report(user_id=None, user_type=None, period_days=30):
        """Generate detailed user activity report"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)
            
            # Build base query
            if user_id:
                # Specific user report
                user = User.query.get(user_id)
                if not user:
                    return {'success': False, 'error': 'User not found'}
                users = [user]
                report_type = 'individual'
                report_title = f"Activity Report for {user.full_name}"
            else:
                # All users of a specific type
                query = User.query
                if user_type:
                    query = query.filter_by(user_type=user_type)
                users = query.all()
                report_type = 'group'
                report_title = f"Activity Report - {user_type.title() if user_type else 'All'} Users"
            
            report_data = {
                'report_info': {
                    'title': report_title,
                    'type': report_type,
                    'period_days': period_days,
                    'start_date': start_date.date().isoformat(),
                    'end_date': end_date.date().isoformat(),
                    'user_count': len(users)
                },
                'users': []
            }
            
            total_bookings = 0
            total_revenue = 0
            
            for user in users:
                user_data = {
                    'id': user.id,
                    'name': user.full_name,
                    'email': user.email,
                    'user_type': user.user_type,
                    'is_active': user.is_active,
                    'joined_date': user.created_at.date().isoformat(),
                    'activity': {}
                }
                
                if user.user_type == 'player':
                    player = Player.query.filter_by(user_id=user.id).first()
                    if player:
                        # Player bookings
                        bookings = Booking.query.filter(
                            Booking.player_id == player.id,
                            Booking.created_at.between(start_date, end_date)
                        ).all()
                        
                        booking_revenue = sum(b.total_cost or b.calculate_cost() for b in bookings if b.status == 'confirmed')
                        
                        user_data['activity'] = {
                            'total_bookings': len(bookings),
                            'confirmed_bookings': len([b for b in bookings if b.status == 'confirmed']),
                            'cancelled_bookings': len([b for b in bookings if b.status == 'cancelled']),
                            'total_spent': float(booking_revenue),
                            'formatted_spent': f"${booking_revenue:.2f}",
                            'avg_booking_value': float(booking_revenue / len([b for b in bookings if b.status == 'confirmed'])) if any(b.status == 'confirmed' for b in bookings) else 0,
                            'skill_level': player.skill_level,
                            'preferred_location': player.preferred_location
                        }
                        
                        total_bookings += len(bookings)
                        total_revenue += booking_revenue
                
                elif user.user_type == 'owner':
                    # Owner courts and revenue
                    courts = Court.query.filter_by(owner_id=user.id).all()
                    
                    owner_bookings = db.session.query(Booking).join(Court).filter(
                        Court.owner_id == user.id,
                        Booking.created_at.between(start_date, end_date)
                    ).all()
                    
                    owner_revenue = sum(b.total_cost or b.calculate_cost() for b in owner_bookings if b.status == 'confirmed')
                    
                    user_data['activity'] = {
                        'total_courts': len(courts),
                        'active_courts': len([c for c in courts if c.is_active]),
                        'total_bookings_received': len(owner_bookings),
                        'confirmed_bookings': len([b for b in owner_bookings if b.status == 'confirmed']),
                        'revenue_earned': float(owner_revenue),
                        'formatted_revenue': f"${owner_revenue:.2f}",
                        'avg_booking_value': float(owner_revenue / len([b for b in owner_bookings if b.status == 'confirmed'])) if any(b.status == 'confirmed' for b in owner_bookings) else 0,
                        'court_names': [c.name for c in courts]
                    }
                    
                    total_bookings += len(owner_bookings)
                    total_revenue += owner_revenue
                
                # Messages activity
                messages_sent = Message.query.filter(
                    Message.sender_id == user.id,
                    Message.created_at.between(start_date, end_date)
                ).count()
                
                messages_received = Message.query.filter(
                    Message.receiver_id == user.id,
                    Message.created_at.between(start_date, end_date)
                ).count()
                
                user_data['activity']['messages_sent'] = messages_sent
                user_data['activity']['messages_received'] = messages_received
                user_data['activity']['total_messages'] = messages_sent + messages_received
                
                report_data['users'].append(user_data)
            
            # Summary statistics
            report_data['summary'] = {
                'total_bookings': total_bookings,
                'total_revenue': float(total_revenue),
                'formatted_total_revenue': f"${total_revenue:.2f}",
                'avg_bookings_per_user': total_bookings / len(users) if users else 0,
                'avg_revenue_per_user': float(total_revenue / len(users)) if users else 0,
                'most_active_user': max(users, key=lambda u: sum(1 for r in report_data['users'] if r['id'] == u.id and r['activity'].get('total_bookings', 0))).full_name if users and total_bookings > 0 else None
            }
            
            return {
                'success': True,
                'report': report_data
            }
            
        except Exception as e:
            return {'success': False, 'error': f'User activity report generation failed: {str(e)}'}
    
    @staticmethod
    def system_performance_metrics(period_days=30):
        """Generate system performance and health metrics"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)
            
            # Booking trends
            daily_bookings = db.session.query(
                func.date(Booking.created_at).label('date'),
                func.count(Booking.id).label('count'),
                Booking.status
            ).filter(
                Booking.created_at.between(start_date, end_date)
            ).group_by(
                func.date(Booking.created_at),
                Booking.status
            ).order_by('date').all()
            
            # User registration trends
            daily_registrations = db.session.query(
                func.date(User.created_at).label('date'),
                func.count(User.id).label('count'),
                User.user_type
            ).filter(
                User.created_at.between(start_date, end_date)
            ).group_by(
                func.date(User.created_at),
                User.user_type
            ).order_by('date').all()
            
            # Revenue trends
            daily_revenue = db.session.query(
                func.date(Booking.booking_date).label('date'),
                func.sum(Court.hourly_rate * 
                        func.extract('hour', Booking.end_time - Booking.start_time)).label('revenue')
            ).join(Court).filter(
                Booking.status == 'confirmed',
                Booking.booking_date.between(start_date.date(), end_date.date())
            ).group_by(func.date(Booking.booking_date)).order_by('date').all()
            
            # Peak usage times
            hourly_usage = db.session.query(
                func.extract('hour', Booking.start_time).label('hour'),
                func.count(Booking.id).label('booking_count')
            ).filter(
                Booking.status == 'confirmed',
                Booking.booking_date.between(start_date.date(), end_date.date())
            ).group_by(func.extract('hour', Booking.start_time)).all()
            
            # Popular locations
            location_popularity = db.session.query(
                Court.location,
                func.count(Booking.id).label('booking_count'),
                func.count(func.distinct(Court.id)).label('court_count')
            ).join(Booking).filter(
                Booking.status == 'confirmed',
                Booking.booking_date.between(start_date.date(), end_date.date())
            ).group_by(Court.location).order_by(
                func.count(Booking.id).desc()
            ).all()
            
            # Court utilization rates
            court_utilization = db.session.query(
                Court.id,
                Court.name,
                Court.location,
                User.full_name.label('owner_name'),
                func.count(Booking.id).label('total_bookings'),
                func.sum(
                    func.case([(Booking.status == 'confirmed', 1)], else_=0)
                ).label('confirmed_bookings')
            ).join(User, Court.owner_id == User.id).outerjoin(
                Booking, and_(
                    Booking.court_id == Court.id,
                    Booking.booking_date.between(start_date.date(), end_date.date())
                )
            ).group_by(
                Court.id, Court.name, Court.location, User.full_name
            ).order_by(func.count(Booking.id).desc()).all()
            
            # Problem areas (high cancellation rates)
            problem_analysis = db.session.query(
                Court.id,
                Court.name,
                Court.location,
                User.full_name.label('owner_name'),
                func.count(Booking.id).label('total_bookings'),
                func.sum(
                    func.case([(Booking.status == 'cancelled', 1)], else_=0)
                ).label('cancelled_bookings'),
                func.sum(
                    func.case([(Booking.status == 'rejected', 1)], else_=0)
                ).label('rejected_bookings')
            ).join(User, Court.owner_id == User.id).outerjoin(Booking).filter(
                Booking.booking_date.between(start_date.date(), end_date.date())
            ).group_by(
                Court.id, Court.name, Court.location, User.full_name
            ).having(func.count(Booking.id) > 5).all()
            
            # Format the data
            metrics = {
                'period': {
                    'start_date': start_date.date().isoformat(),
                    'end_date': end_date.date().isoformat(),
                    'days': period_days
                },
                'booking_trends': {
                    'daily_data': [
                        {
                            'date': str(item.date),
                            'count': item.count,
                            'status': item.status
                        } for item in daily_bookings
                    ]
                },
                'registration_trends': {
                    'daily_data': [
                        {
                            'date': str(item.date),
                            'count': item.count,
                            'user_type': item.user_type
                        } for item in daily_registrations
                    ]
                },
                'revenue_trends': {
                    'daily_data': [
                        {
                            'date': str(item.date),
                            'revenue': float(item.revenue or 0),
                            'formatted_revenue': f"${item.revenue or 0:.2f}"
                        } for item in daily_revenue
                    ]
                },
                'peak_times': [
                    {
                        'hour': int(item.hour),
                        'formatted_hour': f"{int(item.hour):02d}:00",
                        'booking_count': item.booking_count
                    } for item in hourly_usage
                ],
                'popular_locations': [
                    {
                        'location': item.location,
                        'booking_count': item.booking_count,
                        'court_count': item.court_count,
                        'avg_bookings_per_court': float(item.booking_count / item.court_count) if item.court_count > 0 else 0
                    } for item in location_popularity
                ],
                'court_performance': [
                    {
                        'court_id': item.id,
                        'court_name': item.name,
                        'location': item.location,
                        'owner_name': item.owner_name,
                        'total_bookings': item.total_bookings or 0,
                        'confirmed_bookings': item.confirmed_bookings or 0,
                        'utilization_rate': float((item.confirmed_bookings or 0) / period_days * 7),  # bookings per week
                        'approval_rate': float((item.confirmed_bookings or 0) / (item.total_bookings or 1) * 100)
                    } for item in court_utilization
                ],
                'problem_areas': [
                    {
                        'court_id': item.id,
                        'court_name': item.name,
                        'location': item.location,
                        'owner_name': item.owner_name,
                        'total_bookings': item.total_bookings or 0,
                        'cancelled_bookings': item.cancelled_bookings or 0,
                        'rejected_bookings': item.rejected_bookings or 0,
                        'problem_rate': float(((item.cancelled_bookings or 0) + (item.rejected_bookings or 0)) / (item.total_bookings or 1) * 100)
                    } for item in problem_analysis
                ]
            }
            
            return {
                'success': True,
                'metrics': metrics,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Performance metrics generation failed: {str(e)}'}
    
    @staticmethod
    def generate_business_insights(period_days=90):
        """Generate business insights and recommendations"""
        try:
            # Get performance metrics as base data
            performance = ReportService.system_performance_metrics(period_days)
            if not performance['success']:
                return {'success': False, 'error': 'Failed to get performance data'}
            
            metrics = performance['metrics']
            
            insights = {
                'period': metrics['period'],
                'key_insights': [],
                'recommendations': [],
                'opportunities': [],
                'concerns': []
            }
            
            # Analyze booking trends
            total_bookings = sum(item['count'] for item in metrics['booking_trends']['daily_data'])
            confirmed_bookings = sum(item['count'] for item in metrics['booking_trends']['daily_data'] if item['status'] == 'confirmed')
            
            if total_bookings > 0:
                approval_rate = (confirmed_bookings / total_bookings) * 100
                
                if approval_rate > 80:
                    insights['key_insights'].append({
                        'type': 'positive',
                        'title': 'High Approval Rate',
                        'description': f"Excellent {approval_rate:.1f}% booking approval rate indicates good platform quality",
                        'metric': f"{approval_rate:.1f}%"
                    })
                elif approval_rate < 60:
                    insights['concerns'].append({
                        'type': 'warning',
                        'title': 'Low Approval Rate',
                        'description': f"Only {approval_rate:.1f}% of bookings are being approved",
                        'recommendation': 'Review court owner response times and quality standards'
                    })
            
            # Analyze peak times
            if metrics['peak_times']:
                busiest_hour = max(metrics['peak_times'], key=lambda x: x['booking_count'])
                
                insights['key_insights'].append({
                    'type': 'info',
                    'title': 'Peak Usage Time',
                    'description': f"Most popular booking time is {busiest_hour['formatted_hour']} with {busiest_hour['booking_count']} bookings",
                    'metric': busiest_hour['formatted_hour']
                })
                
                # Check for capacity issues during peak times
                if busiest_hour['booking_count'] > confirmed_bookings * 0.3:  # More than 30% of bookings in one hour
                    insights['opportunities'].append({
                        'type': 'capacity',
                        'title': 'Peak Hour Demand',
                        'description': 'High concentration of bookings during peak hours suggests opportunity for dynamic pricing',
                        'recommendation': 'Consider implementing peak-hour pricing or incentivizing off-peak bookings'
                    })
            
            # Analyze location performance
            if metrics['popular_locations']:
                top_location = metrics['popular_locations'][0]
                
                insights['key_insights'].append({
                    'type': 'positive',
                    'title': 'Most Popular Location',
                    'description': f"{top_location['location']} leads with {top_location['booking_count']} bookings from {top_location['court_count']} courts",
                    'metric': f"{top_location['avg_bookings_per_court']:.1f} bookings/court"
                })
                
                # Identify underperforming locations
                if len(metrics['popular_locations']) > 1:
                    bottom_locations = [loc for loc in metrics['popular_locations'] if loc['avg_bookings_per_court'] < top_location['avg_bookings_per_court'] * 0.5]
                    
                    if bottom_locations:
                        insights['concerns'].append({
                            'type': 'performance',
                            'title': 'Underperforming Locations',
                            'description': f"{len(bottom_locations)} locations are performing below 50% of top location average",
                            'recommendation': 'Focus marketing efforts on underperforming areas or review court quality'
                        })
            
            # Analyze court utilization
            if metrics['court_performance']:
                high_performers = [court for court in metrics['court_performance'] if court['approval_rate'] > 90 and court['total_bookings'] > 10]
                low_performers = [court for court in metrics['court_performance'] if court['approval_rate'] < 70 and court['total_bookings'] > 5]
                
                if high_performers:
                    insights['key_insights'].append({
                        'type': 'positive',
                        'title': 'Top Performing Courts',
                        'description': f"{len(high_performers)} courts maintain excellent approval rates above 90%",
                        'metric': f"{len(high_performers)} courts"
                    })
                    
                    insights['opportunities'].append({
                        'type': 'expansion',
                        'title': 'Successful Court Model',
                        'description': 'Identify what makes top courts successful and replicate those features',
                        'recommendation': 'Study high-performing courts and share best practices with other owners'
                    })
                
                if low_performers:
                    insights['concerns'].append({
                        'type': 'quality',
                        'title': 'Courts Need Attention',
                        'description': f"{len(low_performers)} courts have approval rates below 70%",
                        'recommendation': 'Reach out to court owners to improve responsiveness and quality'
                    })
            
            # Analyze problem areas
            if metrics['problem_areas']:
                high_problem_courts = [court for court in metrics['problem_areas'] if court['problem_rate'] > 30]
                
                if high_problem_courts:
                    insights['concerns'].append({
                        'type': 'critical',
                        'title': 'High Cancellation Courts',
                        'description': f"{len(high_problem_courts)} courts have cancellation/rejection rates above 30%",
                        'recommendation': 'Urgent review needed - these courts may harm platform reputation'
                    })
            
            # Revenue analysis
            total_revenue = sum(item['revenue'] for item in metrics['revenue_trends']['daily_data'])
            if metrics['revenue_trends']['daily_data']:
                avg_daily_revenue = total_revenue / len(metrics['revenue_trends']['daily_data'])
                
                insights['key_insights'].append({
                    'type': 'financial',
                    'title': 'Revenue Performance',
                    'description': f"Platform generated ${total_revenue:.2f} in {period_days} days",
                    'metric': f"${avg_daily_revenue:.2f}/day"
                })
                
                # Check revenue trends
                recent_days = metrics['revenue_trends']['daily_data'][-7:]  # Last week
                early_days = metrics['revenue_trends']['daily_data'][:7]   # First week
                
                if len(recent_days) >= 7 and len(early_days) >= 7:
                    recent_avg = sum(day['revenue'] for day in recent_days) / len(recent_days)
                    early_avg = sum(day['revenue'] for day in early_days) / len(early_days)
                    
                    if recent_avg > early_avg * 1.1:  # 10% growth
                        insights['opportunities'].append({
                            'type': 'growth',
                            'title': 'Revenue Growth Trend',
                            'description': f"Revenue trending upward: ${recent_avg:.2f}/day vs ${early_avg:.2f}/day",
                            'recommendation': 'Capitalize on growth momentum with targeted marketing'
                        })
                    elif recent_avg < early_avg * 0.9:  # 10% decline
                        insights['concerns'].append({
                            'type': 'revenue',
                            'title': 'Revenue Decline',
                            'description': f"Revenue declining: ${recent_avg:.2f}/day vs ${early_avg:.2f}/day",
                            'recommendation': 'Investigate causes and implement retention strategies'
                        })
            
            # Generate overall recommendations
            insights['recommendations'] = [
                {
                    'priority': 'high',
                    'category': 'user_experience',
                    'title': 'Improve Response Times',
                    'description': 'Implement automated reminders for court owners to respond to bookings within 24 hours'
                },
                {
                    'priority': 'medium',
                    'category': 'revenue',
                    'title': 'Dynamic Pricing',
                    'description': 'Consider implementing peak-hour pricing to optimize revenue during high-demand periods'
                },
                {
                    'priority': 'medium',
                    'category': 'growth',
                    'title': 'Location Expansion',
                    'description': 'Focus on recruiting court owners in underserved but promising locations'
                },
                {
                    'priority': 'low',
                    'category': 'retention',
                    'title': 'Loyalty Program',
                    'description': 'Develop a player loyalty program to increase booking frequency and retention'
                }
            ]
            
            return {
                'success': True,
                'insights': insights,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Business insights generation failed: {str(e)}'}
    
    @staticmethod
    def export_report_data(report_type, **kwargs):
        """Export report data in various formats (JSON, CSV data structure)"""
        try:
            if report_type == 'admin_dashboard':
                data = ReportService.generate_admin_dashboard_stats()
            elif report_type == 'user_activity':
                data = ReportService.create_user_activity_report(**kwargs)
            elif report_type == 'system_performance':
                data = ReportService.system_performance_metrics(kwargs.get('period_days', 30))
            elif report_type == 'business_insights':
                data = ReportService.generate_business_insights(kwargs.get('period_days', 90))
            else:
                return {'success': False, 'error': f'Unknown report type: {report_type}'}
            
            if not data['success']:
                return data
            
            # Prepare export data
            export_data = {
                'report_type': report_type,
                'generated_at': datetime.now().isoformat(),
                'parameters': kwargs,
                'data': data
            }
            
            return {
                'success': True,
                'export_data': export_data,
                'filename_suggestion': f"tennis_matchup_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Report export failed: {str(e)}'}
    
    @staticmethod
    def get_top_performers(period_days=30, limit=10):
        """Get top performing users, courts, and metrics"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)
            
            # Top players by booking count
            top_players = db.session.query(
                Player.id,
                User.full_name,
                User.email,
                func.count(Booking.id).label('booking_count'),
                func.sum(Booking.total_cost).label('total_spent')
            ).join(User).join(Booking).filter(
                Booking.created_at.between(start_date, end_date)
            ).group_by(
                Player.id, User.full_name, User.email
            ).order_by(func.count(Booking.id).desc()).limit(limit).all()
            
            # Top courts by revenue
            top_courts = db.session.query(
                Court.id,
                Court.name,
                Court.location,
                User.full_name.label('owner_name'),
                func.count(Booking.id).label('booking_count'),
                func.sum(Court.hourly_rate * 
                        func.extract('hour', Booking.end_time - Booking.start_time)).label('revenue')
            ).join(User, Court.owner_id == User.id).join(Booking).filter(
                Booking.status == 'confirmed',
                Booking.booking_date.between(start_date.date(), end_date.date())
            ).group_by(
                Court.id, Court.name, Court.location, User.full_name
            ).order_by(func.sum(Court.hourly_rate * 
                              func.extract('hour', Booking.end_time - Booking.start_time)).desc()).limit(limit).all()
            
            # Top owners by revenue
            top_owners = db.session.query(
                User.id,
                User.full_name,
                User.email,
                func.count(func.distinct(Court.id)).label('court_count'),
                func.count(Booking.id).label('total_bookings'),
                func.sum(Court.hourly_rate * 
                        func.extract('hour', Booking.end_time - Booking.start_time)).label('total_revenue')
            ).join(Court, User.id == Court.owner_id).join(Booking).filter(
                User.user_type == 'owner',
                Booking.status == 'confirmed',
                Booking.booking_date.between(start_date.date(), end_date.date())
            ).group_by(
                User.id, User.full_name, User.email
            ).order_by(func.sum(Court.hourly_rate * 
                              func.extract('hour', Booking.end_time - Booking.start_time)).desc()).limit(limit).all()
            
            return {
                'success': True,
                'period': {
                    'days': period_days,
                    'start_date': start_date.date().isoformat(),
                    'end_date': end_date.date().isoformat()
                },
                'top_players': [
                    {
                        'id': p.id,
                        'name': p.full_name,
                        'email': p.email,
                        'booking_count': p.booking_count,
                        'total_spent': float(p.total_spent or 0),
                        'formatted_spent': f"${p.total_spent or 0:.2f}",
                        'avg_booking_value': float((p.total_spent or 0) / p.booking_count) if p.booking_count > 0 else 0
                    } for p in top_players
                ],
                'top_courts': [
                    {
                        'id': c.id,
                        'name': c.name,
                        'location': c.location,
                        'owner_name': c.owner_name,
                        'booking_count': c.booking_count,
                        'revenue': float(c.revenue or 0),
                        'formatted_revenue': f"${c.revenue or 0:.2f}",
                        'avg_booking_value': float((c.revenue or 0) / c.booking_count) if c.booking_count > 0 else 0
                    } for c in top_courts
                ],
                'top_owners': [
                    {
                        'id': o.id,
                        'name': o.full_name,
                        'email': o.email,
                        'court_count': o.court_count,
                        'total_bookings': o.total_bookings,
                        'total_revenue': float(o.total_revenue or 0),
                        'formatted_revenue': f"${o.total_revenue or 0:.2f}",
                        'avg_revenue_per_court': float((o.total_revenue or 0) / o.court_count) if o.court_count > 0 else 0
                    } for o in top_owners
                ]
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Top performers analysis failed: {str(e)}'}