from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, emit, join_room
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_babel import Babel, gettext as _, get_locale
import secrets
import os
import re
from models import db_init, User, InviteToken, Connection, SharedClipboard, DrawingGame, ChatMessage, ReadStatus
from functools import wraps

app = Flask(__name__)

# Security configurations
secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    print("\n" + "="*60)
    print("WARNING: SECRET_KEY not set! Using random key.")
    print("Sessions will be invalidated on restart.")
    print("Set SECRET_KEY environment variable for production.")
    print("="*60 + "\n")
    secret_key = secrets.token_hex(32)

app.config['SECRET_KEY'] = secret_key
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'False') == 'True'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['WTF_CSRF_TIME_LIMIT'] = None  # No time limit for CSRF tokens

# Babel configuration for i18n
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_SUPPORTED_LOCALES'] = ['en', 'zh']
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'

babel = Babel(app)

@babel.localeselector
def get_user_locale():
    # Check if user explicitly set a language
    lang = session.get('language')
    if lang in app.config['BABEL_SUPPORTED_LOCALES']:
        return lang
    # Otherwise, use browser preference
    return request.accept_languages.best_match(app.config['BABEL_SUPPORTED_LOCALES']) or 'en'

# Admin password
admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
if admin_password == 'admin123':
    print("\n" + "="*60)
    print("WARNING: Using default admin password 'admin123'!")
    print("Set ADMIN_PASSWORD environment variable for security.")
    print("="*60 + "\n")
app.config['ADMIN_PASSWORD'] = admin_password

# Configure CORS for SocketIO
allowed_origins = os.environ.get('ALLOWED_ORIGINS', '*')
if allowed_origins == '*':
    print("\n" + "="*60)
    print("WARNING: CORS allows all origins (*)!")
    print("Set ALLOWED_ORIGINS for production.")
    print("="*60 + "\n")

socketio = SocketIO(app, cors_allowed_origins=allowed_origins, async_mode='threading')

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize database
db_init()

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(int(user_id))

# Make get_locale available in templates
@app.context_processor
def inject_locale():
    return {'get_locale': get_locale}

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Validation helpers
def validate_username(username):
    """Validate username: 3-20 alphanumeric characters, underscores allowed"""
    if not username or len(username) < 3 or len(username) > 20:
        return False
    return bool(re.match(r'^[a-zA-Z0-9_]+$', username))

def validate_password(password):
    """Validate password: minimum 8 characters"""
    return password and len(password) >= 8

def validate_connection_access(connection_id, user_id):
    """Check if user has access to this connection"""
    connection = Connection.get_by_id(connection_id)
    return connection and connection.involves_user(user_id)

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in app.config['BABEL_SUPPORTED_LOCALES']:
        session['language'] = lang
    return redirect(request.referrer or url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        admin_token = request.form.get('admin_token', '').strip()
        
        # Validate inputs
        if not validate_username(username):
            return render_template('register.html', error='Username must be 3-20 characters, alphanumeric and underscores only')
        
        if not validate_password(password):
            return render_template('register.html', error='Password must be at least 8 characters')
        
        # Check admin token and username in one go to prevent enumeration
        token_valid = InviteToken.verify_admin_token(admin_token)
        username_exists = User.get_by_username(username) is not None
        
        if not token_valid or username_exists:
            # Generic error to prevent username enumeration
            return render_template('register.html', error='Registration failed. Check your credentials.')
        
        # Create user
        user = User.create(username, password)
        login_user(user)
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per hour")
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        user = User.get_by_username(username)
        if user and user.verify_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        
        return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_token = current_user.get_invite_token()
    connections = current_user.get_connections()
    
    # Add unread counts to each connection
    for conn in connections:
        conn['unread_chat'] = ChatMessage.get_unread_count(conn['id'], current_user.id)
        conn['unread_clipboard'] = ReadStatus.has_unread_clipboard(current_user.id, conn['id'])
        conn['unread_drawing'] = ReadStatus.has_unread_drawing(current_user.id, conn['id'])
    
    return render_template('dashboard.html', user_token=user_token, connections=connections)

@app.route('/refresh_token', methods=['POST'])
@login_required
def refresh_token():
    current_user.refresh_invite_token()
    return jsonify({'success': True})

@app.route('/connect/<token>')
@login_required
def connect_with_token(token):
    # Find user by token
    target_user = User.get_by_invite_token(token)
    
    if not target_user:
        return render_template('error.html', message='Invalid or expired token')
    
    if target_user.id == current_user.id:
        return render_template('error.html', message='Cannot connect with yourself')
    
    # Create connection
    Connection.create(current_user.id, target_user.id)
    
    # Invalidate the token (one-time use)
    InviteToken.invalidate(token)
    
    return redirect(url_for('dashboard'))

@app.route('/connection/<int:connection_id>')
@login_required
def connection_page(connection_id):
    connection = Connection.get_by_id(connection_id)
    
    if not connection or not connection.involves_user(current_user.id):
        return render_template('error.html', message='Connection not found')
    
    other_user = connection.get_other_user(current_user.id)
    return render_template('connection.html', connection=connection, other_user=other_user)

@app.route('/clipboard/<int:connection_id>')
@login_required
def clipboard(connection_id):
    connection = Connection.get_by_id(connection_id)
    
    if not connection or not connection.involves_user(current_user.id):
        return render_template('error.html', message='Connection not found')
    
    clipboard_data = SharedClipboard.get_by_connection(connection_id)
    other_user = connection.get_other_user(current_user.id)
    
    return render_template('clipboard.html', 
                         connection=connection, 
                         other_user=other_user,
                         clipboard_data=clipboard_data)

@app.route('/drawing/<int:connection_id>')
@login_required
def drawing_game(connection_id):
    connection = Connection.get_by_id(connection_id)
    
    if not connection or not connection.involves_user(current_user.id):
        return render_template('error.html', message='Connection not found')
    
    game = DrawingGame.get_by_connection(connection_id)
    other_user = connection.get_other_user(current_user.id)
    
    return render_template('drawing.html', 
                         connection=connection, 
                         other_user=other_user,
                         game=game)

@app.route('/chat/<int:connection_id>')
@login_required
def chat(connection_id):
    connection = Connection.get_by_id(connection_id)
    
    if not connection or not connection.involves_user(current_user.id):
        return render_template('error.html', message='Connection not found')
    
    other_user = connection.get_other_user(current_user.id)
    messages = ChatMessage.get_messages(connection_id)
    unread_count = ChatMessage.get_unread_count(connection_id, current_user.id)
    
    # Mark as read when viewing
    if messages:
        ReadStatus.update_chat_read(current_user.id, connection_id, messages[-1]['id'])
    
    return render_template('chat.html', 
                         connection=connection, 
                         other_user=other_user,
                         messages=messages,
                         unread_count=unread_count)

@app.route('/admin/login', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password', '')
        admin_password = app.config['ADMIN_PASSWORD']
        # Use constant-time comparison to prevent timing attacks
        if secrets.compare_digest(password, admin_password):
            session['is_admin'] = True
            return redirect(url_for('admin_panel'))
        return render_template('admin_login.html', error='Invalid password')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('index'))

@app.route('/admin')
@admin_required
def admin_panel():
    users = User.get_all()
    tokens = InviteToken.get_all_admin_tokens()
    return render_template('admin_panel.html', users=users, tokens=tokens)

@app.route('/admin/create_token', methods=['POST'])
@admin_required
def create_admin_token():
    token = InviteToken.create_admin_token()
    return jsonify({'token': token})

# WebSocket events
@socketio.on('join_clipboard')
def handle_join_clipboard(data):
    connection_id = data.get('connection_id')
    # Validate access
    if not validate_connection_access(connection_id, current_user.id):
        return
    join_room(f'clipboard_{connection_id}')

@socketio.on('clipboard_update')
def handle_clipboard_update(data):
    connection_id = data.get('connection_id')
    user_id = current_user.id
    content = data.get('content', '')
    
    # Validate access
    if not validate_connection_access(connection_id, user_id):
        return
    
    # Limit content length to 100KB
    if len(content) > 100000:
        content = content[:100000]
    
    # Save to database
    SharedClipboard.update(connection_id, user_id, content)
    
    # Broadcast to room
    emit('clipboard_sync', {
        'user_id': user_id,
        'content': content
    }, room=f'clipboard_{connection_id}', include_self=False)

@socketio.on('join_drawing')
def handle_join_drawing(data):
    connection_id = data.get('connection_id')
    # Validate access
    if not validate_connection_access(connection_id, current_user.id):
        return
    join_room(f'drawing_{connection_id}')

@socketio.on('drawing_start')
def handle_drawing_start(data):
    connection_id = data.get('connection_id')
    answer = data.get('answer', '')
    drawer_id = current_user.id
    
    # Validate access
    if not validate_connection_access(connection_id, drawer_id):
        return
    
    # Validate answer (limit to 50 characters)
    answer = answer.strip()[:50]
    if not answer:
        return
    
    # Create new game round
    DrawingGame.create_round(connection_id, drawer_id, answer)
    
    # Notify other player
    emit('game_started', {
        'drawer_id': drawer_id
    }, room=f'drawing_{connection_id}', include_self=False)

@socketio.on('drawing_data')
def handle_drawing_data(data):
    connection_id = data.get('connection_id')
    drawing = data.get('drawing')
    
    # Validate access
    if not validate_connection_access(connection_id, current_user.id):
        return
    
    # Broadcast drawing to other player
    emit('drawing_update', {
        'drawing': drawing
    }, room=f'drawing_{connection_id}', include_self=False)

@socketio.on('drawing_guess')
def handle_drawing_guess(data):
    connection_id = data.get('connection_id')
    guess = data.get('guess', '')
    
    # Validate access
    if not validate_connection_access(connection_id, current_user.id):
        return
    
    game = DrawingGame.get_by_connection(connection_id)
    
    if game:
        result = game.make_guess(guess)
        
        # Send result to both players
        emit('guess_result', {
            'guess': guess,
            'correct': result['correct'],
            'game_over': result['game_over'],
            'answer': result.get('answer')
        }, room=f'drawing_{connection_id}')

# Chat WebSocket events
@socketio.on('join_chat')
def handle_join_chat(data):
    connection_id = data.get('connection_id')
    # Validate access
    if not validate_connection_access(connection_id, current_user.id):
        return
    join_room(f'chat_{connection_id}')

@socketio.on('send_message')
def handle_send_message(data):
    connection_id = data.get('connection_id')
    message = data.get('message', '').strip()
    
    # Validate access
    if not validate_connection_access(connection_id, current_user.id):
        return
    
    # Validate message length (max 1000 chars)
    if not message or len(message) > 1000:
        return
    
    # Save message
    message_id = ChatMessage.create(connection_id, current_user.id, message)
    
    # Broadcast to room
    emit('new_message', {
        'id': message_id,
        'sender_id': current_user.id,
        'sender_name': current_user.username,
        'message': message,
        'created_at': 'just now'
    }, room=f'chat_{connection_id}')

@socketio.on('mark_read')
def handle_mark_read(data):
    connection_id = data.get('connection_id')
    message_id = data.get('message_id')
    
    # Validate access
    if not validate_connection_access(connection_id, current_user.id):
        return
    
    # Update read status
    ReadStatus.update_chat_read(current_user.id, connection_id, message_id)

if __name__ == '__main__':
    socketio.run(app, debug=False, host='0.0.0.0', port=5000, use_reloader=False)
