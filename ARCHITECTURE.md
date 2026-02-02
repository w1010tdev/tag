# Application Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Social Connect Platform                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐   ┌──────────────┐   │
│  │   Frontend   │◄───│   Flask App  │◄──│   Database   │   │
│  │  (Browser)   │    │   (app.py)   │   │  (SQLite)    │   │
│  └──────────────┘    └──────────────┘   └──────────────┘   │
│         ▲                    ▲                               │
│         │                    │                               │
│         └────WebSocket───────┘                               │
│            (Flask-SocketIO)                                  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Component Architecture

### Backend Layer (`app.py`)

**Role**: Application logic, routing, WebSocket handling

**Key Components**:
- Flask application instance
- Route handlers (HTTP endpoints)
- WebSocket event handlers
- Authentication decorators
- Session management

**Routes**:
```
/                        → Homepage
/login                   → User login
/register                → User registration
/dashboard               → User dashboard
/connect/<token>         → Connect via invite token
/connection/<id>         → Connection details
/clipboard/<id>          → Shared clipboard feature
/drawing/<id>            → Drawing game feature
/admin/login             → Admin authentication
/admin                   → Admin panel
/admin/create_token      → Token generation (API)
/refresh_token           → Refresh user token (API)
```

**WebSocket Events**:
```
join_clipboard           → Join clipboard room
clipboard_update         → Send text update
clipboard_sync           → Receive text update
join_drawing             → Join drawing room
drawing_start            → Start new game
drawing_data             → Send drawing strokes
drawing_update           → Receive drawing strokes
drawing_guess            → Submit guess
guess_result             → Receive guess result
```

### Data Layer (`models.py`)

**Role**: Database operations, data models, business logic

**Models**:

1. **User**
   - Authentication and user management
   - Invite token generation and refresh
   - Connection retrieval

2. **InviteToken**
   - Admin token creation
   - Token verification and invalidation
   - One-time use enforcement

3. **Connection**
   - User-to-user relationship
   - Connection validation

4. **SharedClipboard**
   - Real-time text storage
   - Per-connection, per-user content

5. **DrawingGame**
   - Game state management
   - Guess validation
   - Round lifecycle

### Database Schema

```sql
users
├── id (PRIMARY KEY)
├── username (UNIQUE)
├── password_hash
└── created_at

invite_tokens
├── id (PRIMARY KEY)
├── token (UNIQUE)
├── user_id (FOREIGN KEY → users.id)
├── is_admin_token (BOOLEAN)
├── is_used (BOOLEAN)
└── created_at

connections
├── id (PRIMARY KEY)
├── user1_id (FOREIGN KEY → users.id)
├── user2_id (FOREIGN KEY → users.id)
└── created_at

shared_clipboard
├── id (PRIMARY KEY)
├── connection_id (FOREIGN KEY → connections.id)
├── user_id (FOREIGN KEY → users.id)
├── content (TEXT)
└── updated_at

drawing_games
├── id (PRIMARY KEY)
├── connection_id (FOREIGN KEY → connections.id)
├── drawer_id (FOREIGN KEY → users.id)
├── answer (TEXT)
├── guesses_left (INTEGER, default: 3)
├── is_complete (BOOLEAN)
└── created_at
```

### Frontend Layer

**Structure**:
```
templates/
├── base.html              → Base template with navbar
├── index.html             → Landing page
├── login.html             → Login form
├── register.html          → Registration form
├── dashboard.html         → User dashboard with connections
├── clipboard.html         → Shared clipboard interface
├── drawing.html           → Drawing game interface
├── connection.html        → Connection details page
├── admin_login.html       → Admin login
├── admin_panel.html       → Admin panel with token management
└── error.html             → Error display page

static/
└── css/
    └── style.css          → All styling (responsive, modern)
```

**Frontend Features**:
- Responsive design (mobile-first)
- Real-time updates via Socket.IO client
- HTML5 Canvas for drawing
- CSS Grid and Flexbox for layouts
- Touch event support for mobile drawing

## Data Flow Diagrams

### User Registration Flow

```
User → /register
  ↓
Enter credentials + admin_token
  ↓
app.py: verify admin_token
  ↓
models.py: InviteToken.verify_admin_token()
  ↓
models.py: User.create()
  ↓
SQLite: INSERT user
  ↓
Flask-Login: login_user()
  ↓
Redirect to /dashboard
```

### Connection Creation Flow

```
User A → Generate invite token
  ↓
User A → Share link with User B
  ↓
User B → Click /connect/<token>
  ↓
app.py: User.get_by_invite_token()
  ↓
app.py: Connection.create()
  ↓
SQLite: INSERT connection
  ↓
app.py: InviteToken.invalidate()
  ↓
SQLite: UPDATE token (is_used=1)
  ↓
Both users see connection in dashboard
```

### Real-Time Clipboard Sync Flow

```
User A types in clipboard
  ↓
JavaScript: debounce (500ms)
  ↓
Socket.IO emit: clipboard_update
  ↓
app.py: @socketio.on('clipboard_update')
  ↓
models.py: SharedClipboard.update()
  ↓
SQLite: UPDATE/INSERT content
  ↓
Socket.IO emit to room: clipboard_sync
  ↓
User B receives update
  ↓
JavaScript: update textarea value
```

### Drawing Game Flow

```
User A: Start game, enter answer
  ↓
Socket.IO emit: drawing_start
  ↓
app.py: DrawingGame.create_round()
  ↓
SQLite: INSERT game
  ↓
Socket.IO emit to room: game_started
  ↓
User B: Canvas ready for viewing

User A: Draw strokes
  ↓
Socket.IO emit: drawing_data
  ↓
Socket.IO broadcast: drawing_update
  ↓
User B: Canvas displays strokes

User B: Submit guess
  ↓
Socket.IO emit: drawing_guess
  ↓
app.py: DrawingGame.make_guess()
  ↓
SQLite: UPDATE guesses_left or is_complete
  ↓
Socket.IO emit to room: guess_result
  ↓
Both users see result
```

## Security Architecture

### Authentication
- **Password Hashing**: Werkzeug's `generate_password_hash()` with salt
- **Session Management**: Flask-Login with secure cookies
- **Admin Protection**: Decorator `@admin_required` for admin routes
- **Login Required**: Decorator `@login_required` for protected routes

### Token Security
- **One-Time Use**: Tokens invalidated after connection
- **Cryptographically Secure**: `secrets.token_urlsafe(32)` - 256 bits
- **Admin vs User Tokens**: Separate flag in database
- **Token Refresh**: Users can generate new tokens anytime

### WebSocket Security
- **Room-Based**: Each connection has isolated room
- **User Validation**: Check `current_user` before emitting
- **Connection Verification**: Validate user belongs to connection

## Scalability Considerations

### Current Implementation
- SQLite: Suitable for development and small deployments
- Threading async mode: Simple, works for moderate traffic
- In-memory sessions: Single server only

### Production Recommendations
1. **Database**: PostgreSQL or MySQL for better concurrency
2. **WebSocket**: Redis adapter for multi-server setup
3. **Sessions**: Redis or database-backed sessions
4. **Web Server**: Gunicorn or uWSGI with multiple workers
5. **Load Balancer**: nginx with sticky sessions
6. **Caching**: Redis for frequently accessed data

### Horizontal Scaling Setup
```
                   ┌─────────────┐
                   │ Load        │
                   │ Balancer    │
                   │ (nginx)     │
                   └──────┬──────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
    ┌────▼─────┐    ┌────▼─────┐    ┌────▼─────┐
    │ Flask    │    │ Flask    │    │ Flask    │
    │ Worker 1 │    │ Worker 2 │    │ Worker N │
    └────┬─────┘    └────┬─────┘    └────┬─────┘
         │                │                │
         └────────────────┼────────────────┘
                          │
                   ┌──────▼──────┐
                   │   Redis     │
                   │ (SocketIO)  │
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐
                   │ PostgreSQL  │
                   │ (Database)  │
                   └─────────────┘
```

## Extension Points

### Adding New Features

1. **New Page/Feature**:
   - Add route in `app.py`
   - Create template in `templates/`
   - Add styling in `static/css/style.css`
   - Update navigation in `base.html`

2. **New Real-Time Feature**:
   - Add WebSocket events in `app.py`
   - Add JavaScript handlers in template
   - Optionally add database model in `models.py`

3. **New Database Table**:
   - Add model class in `models.py`
   - Add table creation in `db_init()`
   - Add queries and methods to model

4. **New User Property**:
   - Update User model in `models.py`
   - Update registration form
   - Migrate database (add column)

### Example: Adding a Chat Feature

```python
# models.py
class ChatMessage:
    @staticmethod
    def create(connection_id, user_id, message):
        # Save message to database
        
    @staticmethod
    def get_messages(connection_id, limit=50):
        # Retrieve recent messages

# app.py
@app.route('/chat/<int:connection_id>')
@login_required
def chat(connection_id):
    messages = ChatMessage.get_messages(connection_id)
    return render_template('chat.html', messages=messages)

@socketio.on('send_message')
def handle_message(data):
    ChatMessage.create(data['connection_id'], 
                      current_user.id, 
                      data['message'])
    emit('new_message', data, room=f"chat_{data['connection_id']}")
```

## Performance Optimizations

### Current Optimizations
- Debounced clipboard updates (500ms)
- Connection pooling (SQLite)
- Minimal database queries per request
- Efficient WebSocket room management

### Future Optimizations
- Database query caching
- Static file CDN
- Gzip compression
- Asset minification
- Lazy loading for images
- Database indexing on foreign keys

## Monitoring and Debugging

### Development
- Flask debug mode with reloader
- SQL query logging
- Browser console for WebSocket events
- Network tab for HTTP requests

### Production
- Application logging (Python logging module)
- Error tracking (Sentry, Rollbar)
- Performance monitoring (New Relic, DataDog)
- WebSocket connection monitoring
- Database query performance analysis
