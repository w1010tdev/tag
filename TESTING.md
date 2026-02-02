# Manual Testing Guide for Social Connect

This document describes how to manually test all features of the Social Connect application.

## Prerequisites

1. Start the application:
```bash
python app.py
```

2. Open your browser and navigate to `http://localhost:5000`

## Test Scenarios

### 1. Admin Workflow

#### 1.1 Admin Login
1. Navigate to `/admin/login`
2. Enter password: `admin123`
3. Click "Login"
4. **Expected**: Redirected to admin panel

#### 1.2 Generate Registration Token
1. On admin panel, click "Generate New Token"
2. **Expected**: A new token appears in a text box
3. Copy the token for use in user registration

#### 1.3 View Users and Tokens
1. On admin panel, scroll down
2. **Expected**: See tables showing:
   - All registration tokens (with status: Active/Used)
   - All registered users

### 2. User Registration

#### 2.1 Register New User
1. Navigate to `/register`
2. Enter a username (e.g., "alice")
3. Enter a password
4. Paste the admin token from step 1.2
5. Click "Register"
6. **Expected**: Redirected to dashboard, logged in as the new user

### 3. User Dashboard

#### 3.1 View Invite Token
1. After logging in, view the dashboard
2. **Expected**: See your unique invite link displayed
3. **Expected**: See "Copy" and "Refresh Token" buttons

#### 3.2 Refresh Invite Token
1. Click "Refresh Token"
2. Confirm the action
3. **Expected**: Page reloads with a new token
4. **Expected**: Old token is now invalid

### 4. Connecting Users

#### 4.1 Create Connection
1. Open two different browsers (or incognito mode)
2. Register two different users (alice and bob)
3. Copy alice's invite link from her dashboard
4. In bob's browser, paste the link and navigate to it
5. **Expected**: Bob is redirected to his dashboard
6. **Expected**: Both alice and bob see each other in their connections list

#### 4.2 Verify One-Time Token
1. Try using the same invite link again
2. **Expected**: Error message "Invalid or expired token"

### 5. Shared Clipboard Feature

#### 5.1 Access Shared Clipboard
1. From dashboard, click "Clipboard" on a connection
2. **Expected**: See two text areas side by side
3. **Expected**: One labeled with your username, one with the other user's

#### 5.2 Real-Time Sync
1. Type text in your area
2. **Expected**: Text appears in real-time (with ~500ms delay)
3. Open the same connection in another browser
4. Type in that browser's text area
5. **Expected**: Text appears in the first browser's "other user" area in real-time

### 6. Drawing Game Feature

#### 6.1 Start a Game
1. From dashboard, click "Drawing" on a connection
2. Click "Start New Round"
3. Enter a word (e.g., "house")
4. Click "Start Drawing"
5. **Expected**: See a canvas with drawing tools

#### 6.2 Draw
1. Use mouse to draw on the canvas
2. Select different colors with the color picker
3. Adjust brush size with the slider
4. Click "Clear" to clear the canvas
5. **Expected**: All drawing actions work smoothly

#### 6.3 Real-Time Drawing Sync
1. Open the same connection in another browser
2. **Expected**: The other browser shows "The other player is drawing"
3. **Expected**: Drawing appears in real-time on the guesser's screen

#### 6.4 Guessing
1. In the guesser's browser, type a guess
2. Click "Guess"
3. **Expected**: If wrong, see "Wrong guess! Try again" and guesses decrease
4. Type the correct answer
5. Click "Guess"
6. **Expected**: See "Correct! The answer was: [word]"
7. **Expected**: Page reloads to start screen

#### 6.5 Game Over
1. Start a new game
2. Make 3 incorrect guesses
3. **Expected**: See "Game over! The answer was: [word]"
4. **Expected**: Page reloads to start screen

### 7. Mobile Responsiveness

#### 7.1 Mobile View
1. Open the app on a mobile device or use browser dev tools to emulate mobile
2. **Expected**: Navigation collapses appropriately
3. **Expected**: Text areas and canvas resize to fit screen
4. **Expected**: Touch drawing works on canvas

#### 7.2 Tablet View
1. Resize browser to tablet size
2. **Expected**: Layout adapts smoothly
3. **Expected**: All features remain accessible

### 8. Error Handling

#### 8.1 Invalid Admin Token
1. Try to register with an invalid or used admin token
2. **Expected**: See error "Invalid admin token"

#### 8.2 Duplicate Username
1. Try to register with an existing username
2. **Expected**: See error "Username already exists"

#### 8.3 Invalid Login
1. Try to login with wrong credentials
2. **Expected**: See error "Invalid credentials"

#### 8.4 Unauthorized Access
1. Without logging in, try to access `/dashboard`
2. **Expected**: Redirected to login page

### 9. Security Tests

#### 9.1 Password Hashing
1. Check database.db using sqlite3
2. Look at users table
3. **Expected**: Passwords are hashed, not plain text

#### 9.2 Session Management
1. Login, then close browser
2. Reopen and try to access dashboard
3. **Expected**: Redirected to login (session ended)

#### 9.3 Token Invalidation
1. Use an invite token to connect
2. Try using the same token again
3. **Expected**: Token no longer works

## Expected Results Summary

✅ All features should work smoothly
✅ Real-time updates should be instant (within 1 second)
✅ UI should be responsive on all screen sizes
✅ No errors in browser console
✅ Database should persist data correctly
✅ Security features should prevent unauthorized access

## Known Limitations

- This is a development server; use a production WSGI server for deployment
- WebSocket connections require both users to be online simultaneously
- Drawing canvas size is fixed (could be made responsive in future)
