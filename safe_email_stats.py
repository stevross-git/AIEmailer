
# Alternative email stats that doesn't use folder column
@email_bp.route('/stats-safe')
def email_stats_safe():
    """Get email statistics without folder dependency"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            # Get demo user
            from app.models.user import User
            user = User.query.filter_by(azure_id='demo-user-123').first()
            if user:
                user_id = user.id
                session['user_id'] = user_id
        
        if not user_id:
            return jsonify({
                'total_emails': 0,
                'unread_emails': 0,
                'inbox_count': 0,
                'sent_count': 0,
                'today_emails': 0
            })
        
        # Safe queries without folder column
        total_emails = Email.query.filter_by(user_id=user_id).count()
        unread_emails = Email.query.filter_by(user_id=user_id, is_read=False).count()
        
        # Today's emails
        today = datetime.utcnow().date()
        today_emails = Email.query.filter(
            Email.user_id == user_id,
            Email.received_date >= today
        ).count()
        
        return jsonify({
            'total_emails': total_emails,
            'unread_emails': unread_emails,
            'inbox_count': total_emails,  # Assume all emails are inbox
            'sent_count': 0,  # No sent items for demo
            'today_emails': today_emails
        })
    
    except Exception as e:
        current_app.logger.error(f"Safe email stats error: {e}")
        return jsonify({
            'total_emails': 0,
            'unread_emails': 0,
            'inbox_count': 0,
            'sent_count': 0,
            'today_emails': 0
        })
