"""
Main Routes for AI Email Assistant
"""
from flask import Blueprint, render_template, redirect, url_for, session, current_app
from app.models.user import User
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
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('auth.login'))
    
    # Get basic stats
    stats = {
        'total_emails': user.get_email_count(),
        'recent_emails': [email.to_dict() for email in user.get_recent_emails(5)],
        'last_sync': user.last_sync.strftime('%Y-%m-%d %H:%M:%S') if user.last_sync else 'Never'
    }
    
    return render_template('dashboard.html', user=user.to_dict(), stats=stats)

@main_bp.route('/chat')
@login_required
def chat():
    """Chat interface page"""
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('auth.login'))
    
    return render_template('chat.html', user=user.to_dict())

@main_bp.route('/emails')
@login_required
def emails():
    """Email management page"""
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('auth.login'))
    
    return render_template('emails.html', user=user.to_dict())

@main_bp.route('/settings')
@login_required
def settings():
    """User settings page"""
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('auth.login'))
    
    return render_template('settings.html', user=user.to_dict())

@main_bp.route('/health')
def health():
    """Health check endpoint"""
    try:
        # Check database connection
        User.query.first()
        
        # Check Ollama connection
        from app.services.ollama_engine import OllamaService
        ollama = OllamaService()
        ollama_status = ollama.check_health()
        
        # Check vector database
        vector_status = True
        try:
            if hasattr(current_app, 'vector_service'):
                current_app.vector_service.get_collection_info()
        except Exception:
            vector_status = False
        
        return {
            'status': 'healthy',
            'database': 'connected',
            'ollama': 'connected' if ollama_status else 'disconnected',
            'vector_db': 'connected' if vector_status else 'disconnected'
        }, 200
    
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }, 500

@main_bp.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return render_template('errors/404.html'), 404

@main_bp.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    return render_template('errors/500.html'), 500
@main_bp.route('/emails/<int:email_id>')
def email_redirect(email_id):
    """Redirect to email detail page"""
    return redirect(url_for('email.email_detail', email_id=email_id))
