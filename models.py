import sqlite3
import secrets
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = 'database.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def db_init():
    conn = get_db()
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Invite tokens table
    c.execute('''CREATE TABLE IF NOT EXISTS invite_tokens
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  token TEXT UNIQUE NOT NULL,
                  user_id INTEGER,
                  is_admin_token BOOLEAN DEFAULT 0,
                  is_used BOOLEAN DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # Connections table
    c.execute('''CREATE TABLE IF NOT EXISTS connections
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user1_id INTEGER NOT NULL,
                  user2_id INTEGER NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user1_id) REFERENCES users (id),
                  FOREIGN KEY (user2_id) REFERENCES users (id))''')
    
    # Shared clipboard table
    c.execute('''CREATE TABLE IF NOT EXISTS shared_clipboard
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  connection_id INTEGER NOT NULL,
                  user_id INTEGER NOT NULL,
                  content TEXT,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (connection_id) REFERENCES connections (id),
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # Drawing game table
    c.execute('''CREATE TABLE IF NOT EXISTS drawing_games
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  connection_id INTEGER NOT NULL,
                  drawer_id INTEGER NOT NULL,
                  answer TEXT NOT NULL,
                  guesses_left INTEGER DEFAULT 3,
                  is_complete BOOLEAN DEFAULT 0,
                  session_id INTEGER,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (connection_id) REFERENCES connections (id),
                  FOREIGN KEY (drawer_id) REFERENCES users (id),
                  FOREIGN KEY (session_id) REFERENCES drawing_sessions (id))''')
    
    # Drawing sessions table (for multi-round games)
    c.execute('''CREATE TABLE IF NOT EXISTS drawing_sessions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  connection_id INTEGER NOT NULL,
                  creator_id INTEGER NOT NULL,
                  total_rounds INTEGER DEFAULT 6,
                  current_round INTEGER DEFAULT 0,
                  user1_score INTEGER DEFAULT 0,
                  user2_score INTEGER DEFAULT 0,
                  is_active BOOLEAN DEFAULT 1,
                  waiting_for_partner BOOLEAN DEFAULT 1,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (connection_id) REFERENCES connections (id),
                  FOREIGN KEY (creator_id) REFERENCES users (id))''')
    
    # Chat messages table
    c.execute('''CREATE TABLE IF NOT EXISTS chat_messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  connection_id INTEGER NOT NULL,
                  sender_id INTEGER NOT NULL,
                  message TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (connection_id) REFERENCES connections (id),
                  FOREIGN KEY (sender_id) REFERENCES users (id))''')
    
    # Read status table (for tracking what each user has read)
    c.execute('''CREATE TABLE IF NOT EXISTS read_status
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  connection_id INTEGER NOT NULL,
                  last_read_chat_id INTEGER DEFAULT 0,
                  last_read_clipboard_time TIMESTAMP,
                  last_read_drawing_time TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id),
                  FOREIGN KEY (connection_id) REFERENCES connections (id),
                  UNIQUE(user_id, connection_id))''')

    # Connection memories table
    c.execute('''CREATE TABLE IF NOT EXISTS connection_memories
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  connection_id INTEGER NOT NULL,
                  creator_id INTEGER NOT NULL,
                  memory_text TEXT NOT NULL,
                  memory_date TEXT NOT NULL,
                  status TEXT DEFAULT 'pending',
                  approved_by INTEGER,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  approved_at TIMESTAMP,
                  FOREIGN KEY (connection_id) REFERENCES connections (id),
                  FOREIGN KEY (creator_id) REFERENCES users (id),
                  FOREIGN KEY (approved_by) REFERENCES users (id))''')
    
    conn.commit()
    conn.close()

class User:
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False
    
    def get_id(self):
        return str(self.id)
    
    @staticmethod
    def create(username, password):
        conn = get_db()
        c = conn.cursor()
        password_hash = generate_password_hash(password)
        c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                 (username, password_hash))
        user_id = c.lastrowid
        conn.commit()
        conn.close()
        return User(user_id, username, password_hash)
    
    @staticmethod
    def get_by_id(user_id):
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = c.fetchone()
        conn.close()
        if row:
            return User(row['id'], row['username'], row['password_hash'])
        return None
    
    @staticmethod
    def get_by_username(username):
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        row = c.fetchone()
        conn.close()
        if row:
            return User(row['id'], row['username'], row['password_hash'])
        return None
    
    @staticmethod
    def get_by_invite_token(token):
        conn = get_db()
        c = conn.cursor()
        c.execute('''SELECT u.* FROM users u 
                    JOIN invite_tokens t ON u.id = t.user_id 
                    WHERE t.token = ? AND t.is_used = 0 AND t.is_admin_token = 0''', 
                 (token,))
        row = c.fetchone()
        conn.close()
        if row:
            return User(row['id'], row['username'], row['password_hash'])
        return None
    
    @staticmethod
    def get_all():
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM users ORDER BY created_at DESC')
        rows = c.fetchall()
        conn.close()
        return [{'id': row['id'], 'username': row['username'], 'created_at': row['created_at']} 
                for row in rows]
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_invite_token(self):
        conn = get_db()
        c = conn.cursor()
        c.execute('''SELECT token FROM invite_tokens 
                    WHERE user_id = ? AND is_used = 0 AND is_admin_token = 0
                    ORDER BY created_at DESC LIMIT 1''', (self.id,))
        row = c.fetchone()
        
        if not row:
            # Create new token
            token = secrets.token_urlsafe(32)
            c.execute('INSERT INTO invite_tokens (token, user_id) VALUES (?, ?)',
                     (token, self.id))
            conn.commit()
        else:
            token = row['token']
        
        conn.close()
        return token
    
    def refresh_invite_token(self):
        conn = get_db()
        c = conn.cursor()
        # Mark old tokens as used
        c.execute('UPDATE invite_tokens SET is_used = 1 WHERE user_id = ? AND is_admin_token = 0',
                 (self.id,))
        # Create new token
        token = secrets.token_urlsafe(32)
        c.execute('INSERT INTO invite_tokens (token, user_id) VALUES (?, ?)',
                 (token, self.id))
        conn.commit()
        conn.close()
        return token
    
    def get_connections(self):
        conn = get_db()
        c = conn.cursor()
        c.execute('''SELECT c.id, c.created_at,
                    CASE 
                        WHEN c.user1_id = ? THEN u2.username
                        ELSE u1.username
                    END as other_username,
                    CASE 
                        WHEN c.user1_id = ? THEN c.user2_id
                        ELSE c.user1_id
                    END as other_user_id
                    FROM connections c
                    JOIN users u1 ON c.user1_id = u1.id
                    JOIN users u2 ON c.user2_id = u2.id
                    WHERE c.user1_id = ? OR c.user2_id = ?
                    ORDER BY c.created_at DESC''',
                 (self.id, self.id, self.id, self.id))
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]

class InviteToken:
    @staticmethod
    def create_admin_token():
        conn = get_db()
        c = conn.cursor()
        token = secrets.token_urlsafe(32)
        c.execute('INSERT INTO invite_tokens (token, is_admin_token) VALUES (?, 1)',
                 (token,))
        conn.commit()
        conn.close()
        return token
    
    @staticmethod
    def verify_admin_token(token):
        conn = get_db()
        c = conn.cursor()
        c.execute('''SELECT * FROM invite_tokens 
                    WHERE token = ? AND is_admin_token = 1 AND is_used = 0''',
                 (token,))
        row = c.fetchone()
        
        if row:
            # Mark as used
            c.execute('UPDATE invite_tokens SET is_used = 1 WHERE token = ?', (token,))
            conn.commit()
            conn.close()
            return True
        
        conn.close()
        return False
    
    @staticmethod
    def invalidate(token):
        conn = get_db()
        c = conn.cursor()
        c.execute('UPDATE invite_tokens SET is_used = 1 WHERE token = ?', (token,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_all_admin_tokens():
        conn = get_db()
        c = conn.cursor()
        c.execute('''SELECT token, is_used, created_at FROM invite_tokens 
                    WHERE is_admin_token = 1 ORDER BY created_at DESC''')
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]

class Connection:
    def __init__(self, id, user1_id, user2_id, created_at):
        self.id = id
        self.user1_id = user1_id
        self.user2_id = user2_id
        self.created_at = created_at
    
    @staticmethod
    def create(user1_id, user2_id):
        conn = get_db()
        c = conn.cursor()
        
        # Check if connection already exists
        c.execute('''SELECT * FROM connections 
                    WHERE (user1_id = ? AND user2_id = ?) 
                       OR (user1_id = ? AND user2_id = ?)''',
                 (user1_id, user2_id, user2_id, user1_id))
        
        if c.fetchone():
            conn.close()
            return None
        
        c.execute('INSERT INTO connections (user1_id, user2_id) VALUES (?, ?)',
                 (user1_id, user2_id))
        connection_id = c.lastrowid
        conn.commit()
        conn.close()
        return connection_id
    
    @staticmethod
    def get_by_id(connection_id):
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM connections WHERE id = ?', (connection_id,))
        row = c.fetchone()
        conn.close()
        if row:
            return Connection(row['id'], row['user1_id'], row['user2_id'], row['created_at'])
        return None
    
    def involves_user(self, user_id):
        return self.user1_id == user_id or self.user2_id == user_id
    
    def get_other_user(self, user_id):
        if self.user1_id == user_id:
            return User.get_by_id(self.user2_id)
        else:
            return User.get_by_id(self.user1_id)

class SharedClipboard:
    @staticmethod
    def get_by_connection(connection_id):
        conn = get_db()
        c = conn.cursor()
        c.execute('''SELECT sc.*, u.username FROM shared_clipboard sc
                    JOIN users u ON sc.user_id = u.id
                    WHERE sc.connection_id = ?
                    ORDER BY sc.user_id''', (connection_id,))
        rows = c.fetchall()
        conn.close()
        
        result = {}
        for row in rows:
            result[row['user_id']] = {
                'username': row['username'],
                'content': row['content'],
                'updated_at': row['updated_at']
            }
        return result
    
    @staticmethod
    def update(connection_id, user_id, content):
        conn = get_db()
        c = conn.cursor()
        
        # Check if entry exists
        c.execute('''SELECT * FROM shared_clipboard 
                    WHERE connection_id = ? AND user_id = ?''',
                 (connection_id, user_id))
        
        if c.fetchone():
            c.execute('''UPDATE shared_clipboard 
                        SET content = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE connection_id = ? AND user_id = ?''',
                     (content, connection_id, user_id))
        else:
            c.execute('''INSERT INTO shared_clipboard (connection_id, user_id, content)
                        VALUES (?, ?, ?)''',
                     (connection_id, user_id, content))
        
        conn.commit()
        conn.close()

class DrawingSession:
    """Represents a multi-round drawing game session between two users."""
    def __init__(self, id, connection_id, creator_id, total_rounds, current_round, 
                 user1_score, user2_score, is_active, waiting_for_partner):
        self.id = id
        self.connection_id = connection_id
        self.creator_id = creator_id
        self.total_rounds = total_rounds
        self.current_round = current_round
        self.user1_score = user1_score
        self.user2_score = user2_score
        self.is_active = is_active
        self.waiting_for_partner = waiting_for_partner
    
    @staticmethod
    def create(connection_id, creator_id, total_rounds=6):
        """Create a new drawing session."""
        conn = get_db()
        c = conn.cursor()
        
        # Deactivate any existing sessions for this connection
        c.execute('''UPDATE drawing_sessions SET is_active = 0 
                    WHERE connection_id = ? AND is_active = 1''',
                 (connection_id,))
        
        c.execute('''INSERT INTO drawing_sessions 
                    (connection_id, creator_id, total_rounds, waiting_for_partner)
                    VALUES (?, ?, ?, 1)''',
                 (connection_id, creator_id, total_rounds))
        session_id = c.lastrowid
        conn.commit()
        conn.close()
        return session_id
    
    @staticmethod
    def get_active_session(connection_id):
        """Get the active session for a connection."""
        conn = get_db()
        c = conn.cursor()
        c.execute('''SELECT * FROM drawing_sessions 
                    WHERE connection_id = ? AND is_active = 1
                    ORDER BY created_at DESC LIMIT 1''',
                 (connection_id,))
        row = c.fetchone()
        conn.close()
        
        if row:
            return DrawingSession(
                row['id'], row['connection_id'], row['creator_id'],
                row['total_rounds'], row['current_round'],
                row['user1_score'], row['user2_score'],
                row['is_active'], row['waiting_for_partner']
            )
        return None
    
    @staticmethod
    def get_by_id(session_id):
        """Get a session by ID."""
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM drawing_sessions WHERE id = ?', (session_id,))
        row = c.fetchone()
        conn.close()
        
        if row:
            return DrawingSession(
                row['id'], row['connection_id'], row['creator_id'],
                row['total_rounds'], row['current_round'],
                row['user1_score'], row['user2_score'],
                row['is_active'], row['waiting_for_partner']
            )
        return None
    
    def join_session(self, user_id):
        """A user joins the waiting session."""
        if user_id == self.creator_id:
            return False  # Creator can't join their own session
        
        conn = get_db()
        c = conn.cursor()
        c.execute('''UPDATE drawing_sessions SET waiting_for_partner = 0 
                    WHERE id = ?''', (self.id,))
        conn.commit()
        conn.close()
        self.waiting_for_partner = False
        return True
    
    def start_next_round(self, drawer_id, answer):
        """Start the next round with the given drawer and answer."""
        conn = get_db()
        c = conn.cursor()
        
        # Complete any existing rounds for this session
        c.execute('''UPDATE drawing_games SET is_complete = 1 
                    WHERE session_id = ? AND is_complete = 0''',
                 (self.id,))
        
        # Create new round
        c.execute('''INSERT INTO drawing_games 
                    (connection_id, drawer_id, answer, session_id)
                    VALUES (?, ?, ?, ?)''',
                 (self.connection_id, drawer_id, answer, self.id))
        
        # Increment round counter
        c.execute('''UPDATE drawing_sessions SET current_round = current_round + 1 
                    WHERE id = ?''', (self.id,))
        
        conn.commit()
        conn.close()
        self.current_round += 1
    
    def update_score(self, winner_id):
        """Update score when a round is won."""
        conn = get_db()
        c = conn.cursor()
        
        # Get connection to determine which user
        c.execute('SELECT user1_id, user2_id FROM connections WHERE id = ?',
                 (self.connection_id,))
        row = c.fetchone()
        
        if row:
            if winner_id == row['user1_id']:
                c.execute('''UPDATE drawing_sessions SET user1_score = user1_score + 1 
                            WHERE id = ?''', (self.id,))
                self.user1_score += 1
            else:
                c.execute('''UPDATE drawing_sessions SET user2_score = user2_score + 1 
                            WHERE id = ?''', (self.id,))
                self.user2_score += 1
        
        conn.commit()
        conn.close()
    
    def end_session(self):
        """End the session."""
        conn = get_db()
        c = conn.cursor()
        c.execute('''UPDATE drawing_sessions SET is_active = 0 WHERE id = ?''',
                 (self.id,))
        conn.commit()
        conn.close()
        self.is_active = False
    
    def is_session_complete(self):
        """Check if all rounds are complete."""
        return self.current_round >= self.total_rounds
    
    def get_next_drawer(self, connection):
        """Determine who should draw next (alternating)."""
        # Odd rounds: user1 draws, Even rounds: user2 draws
        if self.current_round % 2 == 0:
            return connection.user1_id
        else:
            return connection.user2_id

class DrawingGame:
    def __init__(self, id, connection_id, drawer_id, answer, guesses_left, is_complete):
        self.id = id
        self.connection_id = connection_id
        self.drawer_id = drawer_id
        self.answer = answer
        self.guesses_left = guesses_left
        self.is_complete = is_complete
    
    @staticmethod
    def create_round(connection_id, drawer_id, answer):
        conn = get_db()
        c = conn.cursor()
        
        # Mark previous games as complete
        c.execute('''UPDATE drawing_games SET is_complete = 1 
                    WHERE connection_id = ? AND is_complete = 0''',
                 (connection_id,))
        
        # Create new game
        c.execute('''INSERT INTO drawing_games (connection_id, drawer_id, answer)
                    VALUES (?, ?, ?)''',
                 (connection_id, drawer_id, answer))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_by_connection(connection_id):
        conn = get_db()
        c = conn.cursor()
        c.execute('''SELECT * FROM drawing_games 
                    WHERE connection_id = ? AND is_complete = 0
                    ORDER BY created_at DESC LIMIT 1''',
                 (connection_id,))
        row = c.fetchone()
        conn.close()
        
        if row:
            return DrawingGame(row['id'], row['connection_id'], row['drawer_id'],
                             row['answer'], row['guesses_left'], row['is_complete'])
        return None
    
    def make_guess(self, guess):
        conn = get_db()
        c = conn.cursor()
        
        correct = guess.lower().strip() == self.answer.lower().strip()
        
        if correct or self.guesses_left <= 1:
            # Game over
            c.execute('UPDATE drawing_games SET is_complete = 1 WHERE id = ?', (self.id,))
            conn.commit()
            conn.close()
            return {
                'correct': correct,
                'game_over': True,
                'answer': self.answer
            }
        else:
            # Decrease guesses
            c.execute('''UPDATE drawing_games SET guesses_left = guesses_left - 1 
                        WHERE id = ?''', (self.id,))
            conn.commit()
            conn.close()
            return {
                'correct': False,
                'game_over': False
            }

class ChatMessage:
    def __init__(self, id, connection_id, sender_id, message, created_at):
        self.id = id
        self.connection_id = connection_id
        self.sender_id = sender_id
        self.message = message
        self.created_at = created_at
    
    @staticmethod
    def create(connection_id, sender_id, message):
        conn = get_db()
        c = conn.cursor()
        c.execute('''INSERT INTO chat_messages (connection_id, sender_id, message)
                    VALUES (?, ?, ?)''',
                 (connection_id, sender_id, message))
        message_id = c.lastrowid
        conn.commit()
        conn.close()
        return message_id
    
    @staticmethod
    def get_messages(connection_id, limit=50, after_id=0):
        conn = get_db()
        c = conn.cursor()
        c.execute('''SELECT cm.*, u.username FROM chat_messages cm
                    JOIN users u ON cm.sender_id = u.id
                    WHERE cm.connection_id = ? AND cm.id > ?
                    ORDER BY cm.created_at DESC LIMIT ?''',
                 (connection_id, after_id, limit))
        rows = c.fetchall()
        conn.close()
        
        messages = []
        for row in rows:
            messages.append({
                'id': row['id'],
                'sender_id': row['sender_id'],
                'sender_name': row['username'],
                'message': row['message'],
                'created_at': row['created_at']
            })
        return list(reversed(messages))  # Return oldest first
    
    @staticmethod
    def get_unread_count(connection_id, user_id):
        """Get count of unread messages for a user in a connection"""
        conn = get_db()
        c = conn.cursor()
        
        # Get last read message id
        c.execute('''SELECT last_read_chat_id FROM read_status
                    WHERE user_id = ? AND connection_id = ?''',
                 (user_id, connection_id))
        row = c.fetchone()
        last_read_id = row['last_read_chat_id'] if row else 0
        
        # Count messages after last read that aren't from this user
        c.execute('''SELECT COUNT(*) as count FROM chat_messages
                    WHERE connection_id = ? AND id > ? AND sender_id != ?''',
                 (connection_id, last_read_id, user_id))
        count = c.fetchone()['count']
        conn.close()
        return count

class ReadStatus:
    @staticmethod
    def update_chat_read(user_id, connection_id, last_message_id):
        """Update the last read message for a user in a connection"""
        conn = get_db()
        c = conn.cursor()
        
        c.execute('''INSERT INTO read_status (user_id, connection_id, last_read_chat_id)
                    VALUES (?, ?, ?)
                    ON CONFLICT(user_id, connection_id) 
                    DO UPDATE SET last_read_chat_id = ?''',
                 (user_id, connection_id, last_message_id, last_message_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def update_clipboard_read(user_id, connection_id):
        """Mark clipboard as read for a user"""
        conn = get_db()
        c = conn.cursor()
        
        c.execute('''INSERT INTO read_status (user_id, connection_id, last_read_clipboard_time)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(user_id, connection_id) 
                    DO UPDATE SET last_read_clipboard_time = CURRENT_TIMESTAMP''',
                 (user_id, connection_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def update_drawing_read(user_id, connection_id):
        """Mark drawing game as read for a user"""
        conn = get_db()
        c = conn.cursor()
        
        c.execute('''INSERT INTO read_status (user_id, connection_id, last_read_drawing_time)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(user_id, connection_id) 
                    DO UPDATE SET last_read_drawing_time = CURRENT_TIMESTAMP''',
                 (user_id, connection_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def has_unread_clipboard(user_id, connection_id):
        """Check if there are unread clipboard updates"""
        conn = get_db()
        c = conn.cursor()
        
        # Get last read time
        c.execute('''SELECT last_read_clipboard_time FROM read_status
                    WHERE user_id = ? AND connection_id = ?''',
                 (user_id, connection_id))
        row = c.fetchone()
        last_read = row['last_read_clipboard_time'] if row else '1970-01-01'
        
        # Check if other user has updated since
        c.execute('''SELECT COUNT(*) as count FROM shared_clipboard
                    WHERE connection_id = ? AND user_id != ? 
                    AND updated_at > ?''',
                 (connection_id, user_id, last_read))
        count = c.fetchone()['count']
        conn.close()
        return count > 0
    
    @staticmethod
    def has_unread_drawing(user_id, connection_id):
        """Check if there are unread drawing game updates"""
        conn = get_db()
        c = conn.cursor()
        
        # Get last read time
        c.execute('''SELECT last_read_drawing_time FROM read_status
                    WHERE user_id = ? AND connection_id = ?''',
                 (user_id, connection_id))
        row = c.fetchone()
        last_read = row['last_read_drawing_time'] if row else '1970-01-01'
        
        # Check if there are new games or guesses since
        c.execute('''SELECT COUNT(*) as count FROM drawing_games
                    WHERE connection_id = ? AND created_at > ?''',
                 (connection_id, last_read))
        count = c.fetchone()['count']
        conn.close()
        return count > 0

class ConnectionMemory:
    def __init__(self, id, connection_id, creator_id, memory_text, memory_date, status, approved_by, created_at, approved_at):
        self.id = id
        self.connection_id = connection_id
        self.creator_id = creator_id
        self.memory_text = memory_text
        self.memory_date = memory_date
        self.status = status
        self.approved_by = approved_by
        self.created_at = created_at
        self.approved_at = approved_at

    @staticmethod
    def create(connection_id, creator_id, memory_text, memory_date):
        conn = get_db()
        c = conn.cursor()
        c.execute('''INSERT INTO connection_memories
                    (connection_id, creator_id, memory_text, memory_date)
                    VALUES (?, ?, ?, ?)''',
                 (connection_id, creator_id, memory_text, memory_date))
        memory_id = c.lastrowid
        conn.commit()
        conn.close()
        return memory_id

    @staticmethod
    def get_for_connection(connection_id):
        conn = get_db()
        c = conn.cursor()
        c.execute('''SELECT cm.*, u.username AS creator_name,
                    au.username AS approver_name
                    FROM connection_memories cm
                    JOIN users u ON cm.creator_id = u.id
                    LEFT JOIN users au ON cm.approved_by = au.id
                    WHERE cm.connection_id = ?
                    ORDER BY cm.memory_date DESC, cm.created_at DESC''',
                 (connection_id,))
        rows = c.fetchall()
        conn.close()
        memories = []
        for row in rows:
            memories.append({
                'id': row['id'],
                'connection_id': row['connection_id'],
                'creator_id': row['creator_id'],
                'creator_name': row['creator_name'],
                'memory_text': row['memory_text'],
                'memory_date': row['memory_date'],
                'status': row['status'],
                'approved_by': row['approved_by'],
                'approver_name': row['approver_name'],
                'created_at': row['created_at'],
                'approved_at': row['approved_at']
            })
        return memories

    @staticmethod
    def approve(connection_id, memory_id, user_id):
        conn = get_db()
        c = conn.cursor()
        c.execute('''UPDATE connection_memories
                    SET status = 'approved',
                        approved_by = ?,
                        approved_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND connection_id = ?
                    AND status = 'pending' AND creator_id != ?''',
                 (user_id, memory_id, connection_id, user_id))
        updated = c.rowcount
        conn.commit()
        conn.close()
        return updated > 0
