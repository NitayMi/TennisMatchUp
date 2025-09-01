from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from models.user import User
from models.player import Player
from models.court import Court
from models.shared_booking import SharedBooking
from models.database import db
from utils.decorators import login_required, player_required
from services.shared_booking_service import SharedBookingService
from datetime import datetime, date
from datetime import datetime, date, timedelta  # הוסף את timedelta

shared_booking_bp = Blueprint('shared_booking', __name__, url_prefix='/shared-booking')

# routes/shared_booking.py - תיקון הנתיב propose_booking

@shared_booking_bp.route('/propose/<int:partner_player_id>')
@login_required
@player_required
def propose_booking(partner_player_id):
    """Show court selection page for joint booking"""
    user_id = session['user_id']
    current_player = Player.query.filter_by(user_id=user_id).first()
    partner_player = Player.query.get(partner_player_id)
    
    if not partner_player:
        flash('Partner player not found.', 'error')
        return redirect(url_for('player.find_matches'))
    
    # Get suggested courts for both players
    suggested_courts = SharedBookingService.suggest_courts_for_pair(
        current_player.id, partner_player.id
    )
    
    # **תיקון: הוסף datetime ו-timedelta לתבנית**
    return render_template('shared_booking/propose.html',
                         current_player=current_player,
                         partner_player=partner_player,
                         suggested_courts=suggested_courts,
                         datetime=datetime,  # הוסף את זה
                         timedelta=timedelta)  # והוסף את זה



@shared_booking_bp.route('/create-proposal', methods=['POST'])
@login_required
@player_required  
def create_proposal():
    """Create a joint booking proposal"""
    user_id = session['user_id']
    current_player = Player.query.filter_by(user_id=user_id).first()
    
    # Get form data
    partner_player_id = request.form.get('partner_player_id', type=int)
    court_id = request.form.get('court_id', type=int)
    booking_date = request.form.get('booking_date')
    start_time = request.form.get('start_time')
    end_time = request.form.get('end_time')
    notes = request.form.get('notes', '').strip()
    
    # Create proposal using service
    result = SharedBookingService.create_booking_proposal(
        player1_id=current_player.id,
        player2_id=partner_player_id,
        court_id=court_id,
        booking_date=booking_date,
        start_time=start_time,
        end_time=end_time,
        notes=notes
    )
    
    if result['success']:
        flash(f'Booking proposal sent successfully! Your partner has 48 hours to respond.', 'success')
        return redirect(url_for('shared_booking.my_proposals'))
    else:
        flash(f'Failed to send proposal: {result["error"]}', 'error')
        return redirect(url_for('shared_booking.propose_booking', partner_player_id=partner_player_id))

@shared_booking_bp.route('/my-proposals')
@login_required
@player_required
def my_proposals():
    """View all shared booking proposals (sent and received)"""
    user_id = session['user_id']
    current_player = Player.query.filter_by(user_id=user_id).first()
    
    # Get all proposals involving this player
    all_proposals = SharedBookingService.get_player_shared_bookings(current_player.id)
    
    # Get pending proposals requiring response
    pending_proposals = SharedBookingService.get_pending_proposals_for_player(current_player.id)
    
    return render_template('shared_booking/my_proposals.html',
                         current_player=current_player,
                         all_proposals=all_proposals,
                         pending_proposals=pending_proposals)

@shared_booking_bp.route('/respond/<int:shared_booking_id>')
@login_required
@player_required
def respond_form(shared_booking_id):
    """Show response form for a proposal"""
    user_id = session['user_id']
    current_player = Player.query.filter_by(user_id=user_id).first()
    
    shared_booking = SharedBooking.query.get_or_404(shared_booking_id)
    
    # Validate user can respond
    if shared_booking.player2_id != current_player.id:
        flash('You are not authorized to respond to this proposal.', 'error')
        return redirect(url_for('shared_booking.my_proposals'))
    
    if shared_booking.status not in ['proposed', 'counter_proposed']:
        flash('This proposal is no longer active.', 'error')
        return redirect(url_for('shared_booking.my_proposals'))
    
    # Get alternative court suggestions if they want to counter-propose
    suggested_courts = SharedBookingService.suggest_courts_for_pair(
        shared_booking.player1_id, shared_booking.player2_id
    )
    
    return render_template('shared_booking/respond.html',
                         shared_booking=shared_booking,
                         current_player=current_player,
                         suggested_courts=suggested_courts)

@shared_booking_bp.route('/submit-response', methods=['POST'])
@login_required
@player_required
def submit_response():
    """Process player's response to a proposal"""
    user_id = session['user_id']
    current_player = Player.query.filter_by(user_id=user_id).first()
    
    shared_booking_id = request.form.get('shared_booking_id', type=int)
    action = request.form.get('action')  # accept, counter_propose, decline
    notes = request.form.get('notes', '').strip()
    
    # Counter-proposal data (if applicable)
    alternative_court_id = request.form.get('alternative_court_id', type=int)
    alternative_date = request.form.get('alternative_date')
    alternative_start_time = request.form.get('alternative_start_time')
    alternative_end_time = request.form.get('alternative_end_time')
    
    # Process response
    result = SharedBookingService.respond_to_proposal(
        shared_booking_id=shared_booking_id,
        responding_player_id=current_player.id,
        action=action,
        notes=notes,
        alternative_court_id=alternative_court_id,
        alternative_date=alternative_date,
        alternative_start_time=alternative_start_time,
        alternative_end_time=alternative_end_time
    )
    
    if result['success']:
        if action == 'accept':
            flash('Proposal accepted! You can now finalize the booking.', 'success')
        elif action == 'counter_propose':
            flash('Counter-proposal sent! Waiting for response.', 'success')
        elif action == 'decline':
            flash('Proposal declined.', 'info')
    else:
        flash(f'Error: {result["error"]}', 'error')
    
    return redirect(url_for('shared_booking.my_proposals'))

@shared_booking_bp.route('/finalize/<int:shared_booking_id>', methods=['POST'])
@login_required
@player_required
def finalize_booking(shared_booking_id):
    """Finalize an accepted shared booking"""
    user_id = session['user_id']
    current_player = Player.query.filter_by(user_id=user_id).first()
    
    result = SharedBookingService.finalize_booking(
        shared_booking_id=shared_booking_id,
        confirming_player_id=current_player.id
    )
    
    if result['success']:
        flash(f'Court booked successfully! Confirmation: {result["booking_details"]["court_name"]} on {result["booking_details"]["date"]}', 'success')
    else:
        flash(f'Booking failed: {result["error"]}', 'error')
    
    return redirect(url_for('shared_booking.my_proposals'))

@shared_booking_bp.route('/cancel/<int:shared_booking_id>', methods=['POST'])
@login_required
@player_required
def cancel_proposal(shared_booking_id):
    """Cancel a shared booking proposal"""
    user_id = session['user_id']
    current_player = Player.query.filter_by(user_id=user_id).first()
    
    shared_booking = SharedBooking.query.get_or_404(shared_booking_id)
    
    # Validate user can cancel
    if current_player.id not in [shared_booking.player1_id, shared_booking.player2_id]:
        flash('You are not authorized to cancel this proposal.', 'error')
        return redirect(url_for('shared_booking.my_proposals'))
    
    reason = request.form.get('reason', '').strip()
    
    try:
        shared_booking.cancel(current_player.id, reason)
        db.session.commit()
        flash('Proposal cancelled successfully.', 'info')
    except Exception as e:
        db.session.rollback()
        flash('Failed to cancel proposal.', 'error')
    
    return redirect(url_for('shared_booking.my_proposals'))

@shared_booking_bp.route('/api/court-availability/<int:court_id>')
@login_required
def check_court_availability(court_id):
    """API endpoint to check court availability for a specific date"""
    booking_date = request.args.get('date')
    
    if not booking_date:
        return jsonify({'error': 'Date parameter required'}), 400
    
    try:
        court = Court.query.get_or_404(court_id)
        available_slots = court.get_available_slots(booking_date)
        
        return jsonify({
            'success': True,
            'court_name': court.name,
            'date': booking_date,
            'available_slots': available_slots
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to check availability'}), 500