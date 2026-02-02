# Social Connect - Modern Networking Platform

A modern, real-time networking platform that allows users to connect and interact through shared clipboards and drawing games.

## Features

- **User Registration & Authentication**: Users can register with admin-provided tokens
- **One-Time Invite Tokens**: Each user can generate unique, refreshable invite tokens to establish connections
- **Shared Clipboard**: Real-time synchronized text areas for seamless collaboration between connected users
- **Drawing Game (Pictionary)**: Interactive drawing and guessing game with 3 attempts per round
- **Admin Panel**: Manage users and generate registration tokens
- **Modern UI**: Beautiful, responsive interface that works on both mobile and desktop
- **Real-Time Sync**: WebSocket-powered instant updates

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Real-Time Communication**: Flask-SocketIO
- **Frontend**: HTML5, CSS3, JavaScript
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

#### Shared Clipboard
- Click "Clipboard" on any connection
- Type in your text area - changes sync in real-time
- See the other person's text updates instantly

#### Drawing Game
1. Click "Drawing" on any connection
2. Click "Start New Round"
3. The drawer enters a word and draws
4. The guesser watches the drawing appear in real-time
5. The guesser has 3 attempts to guess correctly
6. Take turns playing!

## File Structure

```
tag/
├── app.py              # Main Flask application
├── models.py           # Database models and logic
├── requirements.txt    # Python dependencies
├── database.db         # SQLite database (created on first run)
├── templates/          # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── clipboard.html
│   ├── drawing.html
│   ├── admin_login.html
│   ├── admin_panel.html
│   ├── error.html
│   └── connection.html
└── static/
    └── css/
        └── style.css   # Styling
```

## Security Notes

- Change the `ADMIN_PASSWORD` environment variable in production
- Use a strong `SECRET_KEY` in production
- The application uses HTTPS in production environments
- Passwords are hashed using Werkzeug's security utilities
- One-time tokens prevent unauthorized connections

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
