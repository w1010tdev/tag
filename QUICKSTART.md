# Quick Start Guide

Get Social Connect up and running in 5 minutes!

## Installation (1 minute)

```bash
# Clone the repository
git clone https://github.com/w1010tdev/tag.git
cd tag

# Install dependencies
pip install -r requirements.txt
```

## Running the App (30 seconds)

```bash
python app.py
```

The app will start on `http://localhost:5000`

## First Time Setup (3 minutes)

### 1. Admin Setup (1 minute)

1. Open your browser to `http://localhost:5000/admin/login`
2. Login with password: `admin123` (⚠️ Change this for production!)
3. Click "Generate New Token"
4. Copy the token

### 2. Register Your First User (1 minute)

1. Go to `http://localhost:5000/register`
2. Choose a username and password
3. Paste the admin token
4. Click "Register"

### 3. Start Connecting! (1 minute)

1. On your dashboard, copy your invite link
2. Share it with a friend (or open in another browser/device)
3. They click the link to connect with you
4. Now you can use:
   - 📋 **Shared Clipboard** - Real-time text sync
   - 🎨 **Drawing Game** - Play Pictionary together

## That's It! 🎉

You're now ready to:
- Create more admin tokens for new users
- Connect with multiple people
- Use the shared clipboard for collaboration
- Play drawing games with friends

## Next Steps

- Read [README.md](README.md) for detailed documentation
- Check [TESTING.md](TESTING.md) for feature testing guide
- Customize the admin password in production:
  ```bash
  export ADMIN_PASSWORD="your-secure-password"
  python app.py
  ```

## Need Help?

- All pages have clear navigation
- Error messages guide you when something goes wrong
- UI is mobile-friendly - works on any device

## Production Deployment

For production use:
1. Set environment variables:
   ```bash
   export SECRET_KEY="your-random-secret-key"
   export ADMIN_PASSWORD="your-admin-password"
   ```
2. Use a production WSGI server (e.g., gunicorn, uWSGI)
3. Set up HTTPS with a reverse proxy (nginx, Apache)
4. Consider using PostgreSQL instead of SQLite for better concurrency

Enjoy Social Connect! 🚀
