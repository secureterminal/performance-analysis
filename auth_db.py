# ============================================
# FILE 1: auth_db.py (Database Management)
# ============================================
import sqlite3
import hashlib
import os
from datetime import datetime


class AuthDatabase:
    def __init__(self, db_path="users.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with users table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                email TEXT,
                full_name TEXT,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Create sessions table (optional, for tracking)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password, salt=None):
        """Hash password with salt using SHA-256"""
        if salt is None:
            salt = os.urandom(32).hex()
        
        # Combine password and salt, then hash
        password_salt = f"{password}{salt}".encode('utf-8')
        password_hash = hashlib.sha256(password_salt).hexdigest()
        
        return password_hash, salt
    
    def create_user(self, username, password, email=None, full_name=None, role='user'):
        """Create a new user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Hash the password
            password_hash, salt = self.hash_password(password)
            
            # Insert user
            cursor.execute('''
                INSERT INTO users (username, password_hash, salt, email, full_name, role)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, password_hash, salt, email, full_name, role))
            
            conn.commit()
            return True, "User created successfully"
        
        except sqlite3.IntegrityError:
            return False, "Username already exists"
        except Exception as e:
            return False, f"Error: {str(e)}"
        finally:
            conn.close()
    
    def verify_user(self, username, password):
        """Verify user credentials"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get user data
            cursor.execute('''
                SELECT password_hash, salt, is_active, role, full_name
                FROM users WHERE username = ?
            ''', (username,))
            
            result = cursor.fetchone()
            
            if not result:
                return False, "User not found", None
            
            stored_hash, salt, is_active, role, full_name = result
            
            if not is_active:
                return False, "Account is deactivated", None
            
            # Hash the provided password with stored salt
            password_hash, _ = self.hash_password(password, salt)
            
            # Compare hashes
            if password_hash == stored_hash:
                # Update last login
                cursor.execute('''
                    UPDATE users SET last_login = ? WHERE username = ?
                ''', (datetime.now(), username))
                
                # Log session
                cursor.execute('''
                    INSERT INTO sessions (username) VALUES (?)
                ''', (username,))
                
                conn.commit()
                
                user_info = {
                    'username': username,
                    'role': role,
                    'full_name': full_name or username
                }
                
                return True, "Login successful", user_info
            else:
                return False, "Invalid password", None
        
        except Exception as e:
            return False, f"Error: {str(e)}", None
        finally:
            conn.close()
    
    def change_password(self, username, old_password, new_password):
        """Change user password"""
        # First verify old password
        is_valid, message, _ = self.verify_user(username, old_password)
        
        if not is_valid:
            return False, "Invalid current password"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Generate new hash
            new_hash, new_salt = self.hash_password(new_password)
            
            # Update password
            cursor.execute('''
                UPDATE users SET password_hash = ?, salt = ?
                WHERE username = ?
            ''', (new_hash, new_salt, username))
            
            conn.commit()
            return True, "Password changed successfully"
        
        except Exception as e:
            return False, f"Error: {str(e)}"
        finally:
            conn.close()
    
    def get_all_users(self):
        """Get all users (admin function)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT username, email, full_name, role, created_at, last_login, is_active
            FROM users
        ''')
        
        users = cursor.fetchall()
        conn.close()
        
        return users