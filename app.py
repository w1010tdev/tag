from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import secrets
import sqlite3
from datetime import datetime
import os
from models import db_init, User, InviteToken, Connection, SharedClipboard, DrawingGame
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Require admin password to be set via environment variable
if not os.environ.get('ADMIN_PASSWORD'):
    print("\n" + "="*60)
    print("WARNING: ADMIN_PASSWORD environment variable not set!")
    print("Using default password 'admin123' for development only.")
    print("Set ADMIN_PASSWORD environment variable for production.")
    print("="*60 + "\n")
app.config['ADMIN_PASSWORD'] = os.environ.get('ADMIN_PASSWORD', 'admin123')

# Configure CORS for SocketIO - restrict in production
allowed_origins = os.environ.get('ALLOWED_ORIGINS', '*')
if allowed_origins == '*':
    print("\n" + "="*60)
    print("WARNING: CORS is set to allow all origins (*)!")
    print("Set ALLOWED_ORIGINS environment variable for production.")
    print("Example: ALLOWED_ORIGINS=https://yourdomain.com")
    print("="*60 + "\n")
socketio = SocketIO(app, cors_allowed_origins=allowed_origins, async_mode='threading')
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize database
db_init()

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin_token = request.form.get('admin_token')
        
        # Verify admin token
        if not InviteToken.verify_admin_token(admin_token):
            return render_template('register.html', error='Invalid admin token')
        
        # Check if username exists
        if User.get_by_username(username):
            return render_template('register.html', error='Username already exists')
        
        # Create user
        user = User.create(username, password)
        login_user(user)
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
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

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == app.config['ADMIN_PASSWORD']:
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
    join_room(f'clipboard_{connection_id}')

@socketio.on('clipboard_update')
def handle_clipboard_update(data):
    connection_id = data.get('connection_id')
    user_id = current_user.id
    content = data.get('content')
    
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
    join_room(f'drawing_{connection_id}')

@socketio.on('drawing_start')
def handle_drawing_start(data):
    connection_id = data.get('connection_id')
    answer = data.get('answer')
    drawer_id = current_user.id
    
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
    
    # Broadcast drawing to other player
    emit('drawing_update', {
        'drawing': drawing
    }, room=f'drawing_{connection_id}', include_self=False)

@socketio.on('drawing_guess')
def handle_drawing_guess(data):
    connection_id = data.get('connection_id')
    guess = data.get('guess')
    
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

if __name__ == '__main__':
    socketio.run(app, debug=False, host='0.0.0.0', port=5000, use_reloader=False)
