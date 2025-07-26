"""
Main routes for AI Email Assistant
"""
from flask import Blueprint, render_template, redirect, url_for, session, current_app, jsonify
from app.models import db
from app.models.user import User
from app.models.email import Email
from app.utils.auth_helpers import login_required

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Main landing page"""
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard page"""
    try:
        user = User.query.get(session['user_id'])
        if not user:
            session.clear()
            return redirect(url_for('auth.login'))
        
        # Get email statistics
        total_emails = user.get_email_count()
        unread_emails = user.get_unread_email_count()
        
        # Get recent emails
        recent_emails = Email.get_user_emails(user.id, limit=10)
        
        # Get high priority emails
        high_priority_emails = Email.query.filter_by(
            user_id=user.id,
            importance='high'
        ).order_by(Email.received_date.desc()).limit(5).all()
        
        # Prepare statistics
        stats = {
            'total_emails': total_emails,
            'unread_emails': unread_emails,
            'read_emails': total_emails - unread_emails,
            'high_priority_count': len(high_priority_emails),
            'last_sync': user.last_email_sync.strftime('%Y-%m-%d %H:%M:%S') if user.last_email_sync else 'Never',
            'recent_emails': [email.to_dict() for email in recent_emails[:5]],
            'high_priority_emails': [email.to_dict() for email in high_priority_emails]
        }
        
        return render_template('dashboard.html', 
                             user=user.to_dict(), 
                             stats=stats)
        
    except Exception as e:
        current_app.logger.error(f"Dashboard error: {e}")
        return render_template('errors/500.html'), 500

@main_bp.route('/chat')
@login_required
def chat():
    """Chat interface page"""
    try:
        user = User.query.get(session['user_id'])
        if not user:
            session.clear()
            return redirect(url_for('auth.login'))
        
        # Get basic email stats for context
        stats = {
            'total_emails': user.get_email_count(),
            'unread_emails': user.get_unread_email_count()
        }
        
        return render_template('chat.html', user=user.to_dict(), stats=stats)
        
    except Exception as e:
        current_app.logger.error(f"Chat page error: {e}")
        return render_template('errors/500.html'), 500

@main_bp.route('/emails')
@login_required
def emails():
    """Email management page"""
    try:
        user = User.query.get(session['user_id'])
        if not user:
            session.clear()
            return redirect(url_for('auth.login'))
        
        # Get emails with pagination
        page = int(request.args.get('page', 1))
        per_page = 20
        offset = (page - 1) * per_page
        
        emails = Email.get_user_emails(user.id, limit=per_page, offset=offset)
        total_emails = user.get_email_count()
        unread_emails = user.get_unread_email_count()
        
        # Calculate pagination
        total_pages = (total_emails + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        stats = {
            'total_emails': total_emails,
            'unread_emails': unread_emails,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'has_prev': has_prev,
            'has_next': has_next
        }
        
        return render_template('emails.html', 
                             user=user.to_dict(), 
                             emails=[email.to_dict() for email in emails],
                             stats=stats)
        
    except Exception as e:
        current_app.logger.error(f"Emails page error: {e}")
        return render_template('errors/500.html'), 500

@main_bp.route('/emails/<int:email_id>')
def email_redirect(email_id):
    """Redirect to email detail page"""
    return redirect(url_for('email.email_detail', email_id=email_id))

@main_bp.route('/settings')
@login_required
def settings():
    """User settings page"""
    try:
        user = User.query.get(session['user_id'])
        if not user:
            session.clear()
            return redirect(url_for('auth.login'))
        
        # Get user preferences and settings
        settings_data = {
            'email_sync': {
                'auto_sync': True,
                'sync_frequency': 15,  # minutes
                'max_emails': 50
            },
            'notifications': {
                'email_notifications': True,
                'priority_alerts': True,
                'digest_frequency': 'daily'
            },
            'ai_preferences': {
                'auto_analysis': True,
                'response_suggestions': True,
                'priority_detection': True
            }
        }
        
        return render_template('settings.html', 
                             user=user.to_dict(), 
                             settings=settings_data)
        
    except Exception as e:
        current_app.logger.error(f"Settings page error: {e}")
        return render_template('errors/500.html'), 500

@main_bp.route('/health')
def health():
    """Health check endpoint"""
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        
        # Check if we can query users table
        user_count = User.query.count()
        
        # Basic health status
        status = {
            'status': 'healthy',
            'database': 'connected',
            'users': user_count,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Check AI services if available
        try:
            from app.services.ollama_engine import OllamaService
            ollama = OllamaService()
            ollama_status = ollama.check_health()
            status['ai_service'] = 'available' if ollama_status else 'unavailable'
        except ImportError:
            status['ai_service'] = 'not_configured'
        except Exception as e:
            status['ai_service'] = f'error: {str(e)}'
        
        # Check email sync capability
        try:
            from app.services.ms_graph import MSGraphService
            status['graph_service'] = 'configured'
        except ImportError:
            status['graph_service'] = 'not_configured'
        except Exception as e:
            status['graph_service'] = f'error: {str(e)}'
        
        return jsonify(status)
        
    except Exception as e:
        current_app.logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@main_bp.route('/api/status')
def api_status():
    """API status endpoint"""
    try:
        return jsonify({
            'api': 'operational',
            'version': '1.0.0',
            'features': {
                'email_sync': True,
                'ai_analysis': True,
                'chat_interface': True,
                'search': True
            },
            'endpoints': {
                'auth': '/auth/*',
                'email': '/api/email/*',
                'chat': '/api/chat/*'
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Error handlers
@main_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return render_template('errors/404.html', user=user.to_dict() if user else None), 404
    else:
        return render_template('errors/404.html'), 404

@main_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    current_app.logger.error(f"Internal server error: {error}")
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return render_template('errors/500.html', user=user.to_dict() if user else None), 500
    else:
        return render_template('errors/500.html'), 500

# Additional utility routes
@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@main_bp.route('/privacy')
def privacy():
    """Privacy policy page"""
    return render_template('privacy.html')

@main_bp.route('/terms')
def terms():
    """Terms of service page"""
    return render_template('terms.html')

# Import statements for datetime
from datetime import datetime
from flask import request