# Social Connect - Modern Networking Platform

A modern, real-time networking platform that allows users to connect and interact through private chat, shared clipboards, and drawing games.

## Features

### Core Features
- **User Registration & Authentication**: Secure registration with admin-provided tokens
- **One-Time Invite Tokens**: Each user can generate unique, refreshable invite tokens to establish connections
- **Private Chat**: Real-time messaging with Font Awesome icon pack
- **Shared Clipboard**: Real-time synchronized text areas for seamless collaboration
- **Drawing Game (Pictionary)**: Interactive drawing and guessing game with 3 attempts per round
- **Admin Panel**: Manage users and generate registration tokens
- **Modern UI**: Clean, responsive interface optimized for mobile and desktop
- **Real-Time Sync**: WebSocket-powered instant updates

### New Features
- **Read/Unread Status**: Track unread messages, clipboard updates, and game changes
- **Icon Support**: Font Awesome icon-based picker with 20+ options
- **Unread Badges**: Visual indicators for new content on dashboard
- **Mobile Optimized**: Touch-friendly interface for non-technical users

### Security Features
- **CSRF Protection**: Flask-WTF protects all forms
- **Rate Limiting**: Prevents brute force attacks (5-10 attempts/hour)
- **Input Validation**: Username (3-20 alphanumeric), Password (min 8 chars)
- **WebSocket Authorization**: All real-time events are authorized
- **Content Limits**: Prevents abuse (chat 1KB, clipboard 100KB)
- **Secure Sessions**: HTTPOnly and SameSite cookies

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite (7 tables)
- **Real-Time Communication**: Flask-SocketIO
- **Security**: Flask-WTF (CSRF), Flask-Limiter (Rate limiting)
- **Frontend**: HTML5, CSS3, JavaScript, Font Awesome
- **Authentication**: Flask-Login

## Installation

1. Clone the repository:
```bash
git clone https://github.com/w1010tdev/tag.git
cd tag
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables (optional):
```bash
export SECRET_KEY="your-secret-key-here"
export ADMIN_PASSWORD="your-admin-password"
```

If not set, defaults will be used:
- Admin password: `admin123` (change this in production!)

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

### Admin Setup

1. Navigate to `/admin/login`
2. Enter the admin password (default: `admin123`)
3. Generate registration tokens for new users
4. Share tokens with users who want to register

### User Registration

1. Navigate to `/register`
2. Enter a username and password
3. Provide the admin token you received
4. Click "Register"

### Connecting with Others

1. After logging in, you'll see your unique invite token on the dashboard
2. Share your invite link with someone you want to connect with
3. They can click the link to establish a connection
4. The token will be automatically invalidated after one use
5. You can refresh your token anytime to generate a new one

### Using Features

#### Private Chat
- Click "Chat" on any connection
- Type messages and send with Enter or click send button
- Click icon button to open the icon picker
- See unread count badge on dashboard
- Messages sync in real-time

#### Shared Clipboard
- Click "Clipboard" on any connection
- Type in your text area - changes sync in real-time
- Use the toolbar to switch between text, handwriting, moods, stickers, and shared memories
- See the other person's text updates instantly
- Unread indicator shows when other person updates

#### Drawing Game
1. Click "Drawing" on any connection
2. Click "Start New Round"
3. The drawer enters a word and draws
4. The guesser watches the drawing appear in real-time
5. The guesser has 3 attempts to guess correctly
6. Take turns playing!
7. Unread indicator shows new games

### Requirements for Users
- **Username**: 3-20 characters, letters, numbers, and underscores only
- **Password**: Minimum 8 characters

## File Structure

```
tag/
├── app.py              # Main Flask application
├── models.py           # Database models and logic
├── requirements.txt    # Python dependencies
├── database.db         # SQLite database (created on first run)
├── templates/          # HTML templates
│   ├── base.html              # Base template with Font Awesome
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html         # With unread badges
│   ├── chat.html             # New: Private chat
│   ├── clipboard.html
│   ├── drawing.html
│   ├── admin_login.html
│   ├── admin_panel.html
│   ├── error.html
│   └── connection.html
└── static/
    └── css/
        └── style.css   # Styling (includes chat styles)
```

## Database Schema

The application uses SQLite with 7 tables:

1. **users** - User accounts with hashed passwords
2. **invite_tokens** - Admin and user invitation tokens
3. **connections** - User-to-user relationships
4. **shared_clipboard** - Real-time synchronized text
5. **drawing_games** - Game state and guesses
6. **chat_messages** - Private chat messages (NEW)
7. **read_status** - Read/unread tracking (NEW)

## Security Notes

- **CSRF Protection**: All forms protected with Flask-WTF
- **Rate Limiting**: Login (10/hr), Register (5/hr), Admin (5/hr)
- **Input Validation**: Usernames (3-20 alphanumeric), Passwords (min 8 chars)
- **Content Limits**: Chat (1KB), Clipboard (100KB), Answers (50 chars)
- **WebSocket Auth**: All real-time events check user permissions
- **Password Hashing**: Werkzeug PBKDF2 with salt
- **Session Security**: HTTPOnly, SameSite cookies
- **Admin Password**: Use constant-time comparison
- Change `ADMIN_PASSWORD` and `SECRET_KEY` in production

## Extending Functionality

The application is designed to be easily extensible:

1. **New Features**: Add new routes in `app.py` and corresponding templates
2. **Database Models**: Extend `models.py` with new tables and methods
3. **WebSocket Events**: Add new socket events in `app.py` for real-time features
4. **Styling**: Modify `static/css/style.css` for design changes

## Mobile Support

The application is fully responsive and optimized for:
- Desktop browsers
- Tablets
- Mobile phones (touch events supported for drawing)

## License

See LICENSE file for details.

## Support

For issues or questions, please open an issue on GitHub.
