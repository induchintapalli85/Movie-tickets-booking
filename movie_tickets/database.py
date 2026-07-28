import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instagram.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            profile_pic TEXT NOT NULL,
            bio TEXT,
            is_following INTEGER DEFAULT 0
        )
    ''')

    # Create posts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            image_url TEXT NOT NULL,
            location TEXT,
            likes_count INTEGER DEFAULT 0,
            caption TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Create comments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            comment_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts (id)
        )
    ''')

    # Create stories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            image_url TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Create likes table to track which posts the current user (Chinna Medida) has liked
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            UNIQUE(post_id, user_id)
        )
    ''')

    # Seed data if table is empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        # Seed users
        users_data = [
            ("chinna_medida", "Chinna Medida", "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=500", "Web Developer", 0),
            ("priya_sharma", "Priya Sharma", "https://images.unsplash.com/photo-1494790108377-be9c29b29330?q=80&w=500", "Travel Enthusiast 🗺️", 0),
            ("rahul_verma", "Rahul Verma", "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=500", "Weekend explorer 📸", 0),
            ("anu_style", "Anu", "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?q=80&w=500", "Fashion Designer 👗", 0),
            ("satish_k", "Satish", "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?q=80&w=500", "Tech Geek 💻", 0),
            ("keerthi_official", "Keerthi", "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?q=80&w=500", "Popular Creator 🌟", 0),
            ("ajay_dev", "Ajay", "https://images.unsplash.com/photo-1521119989659-a83eee488004?q=80&w=500", "Fitness Coach 🏋️", 0),
            ("sneha_r", "Sneha", "https://images.unsplash.com/photo-1504593811423-6dd665756598?q=80&w=500", "Nature Lover 🌱", 0),
            ("kiran_kumar", "Kiran", "https://images.unsplash.com/photo-1488426862026-3ee34a7d66df?q=80&w=500", "Foodie 🍕", 0)
        ]
        cursor.executemany('''
            INSERT INTO users (username, full_name, profile_pic, bio, is_following)
            VALUES (?, ?, ?, ?, ?)
        ''', users_data)

        # Seed stories
        # User IDs map: chinna_medida=1, priya_sharma=2, rahul_verma=3, anu_style=4, satish_k=5, keerthi_official=6, ajay_dev=7, sneha_r=8, kiran_kumar=9
        stories_data = [
            (2, "https://images.unsplash.com/photo-1494790108377-be9c29b29330?q=80&w=500"),
            (3, "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=500"),
            (4, "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?q=80&w=500"),
            (5, "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?q=80&w=500"),
            (6, "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?q=80&w=500"),
            (7, "https://images.unsplash.com/photo-1521119989659-a83eee488004?q=80&w=500"),
            (8, "https://images.unsplash.com/photo-1504593811423-6dd665756598?q=80&w=500"),
            (9, "https://images.unsplash.com/photo-1488426862026-3ee34a7d66df?q=80&w=500")
        ]
        cursor.executemany('''
            INSERT INTO stories (user_id, image_url)
            VALUES (?, ?)
        ''', stories_data)

        # Seed posts
        posts_data = [
            (2, "https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=1200", "Mumbai, India", 12450, "Beautiful nature view 🌄"),
            (3, "https://images.unsplash.com/photo-1517841905240-472988babdf9?q=80&w=1200", "Hyderabad", 8320, "Weekend vibes ✨")
        ]
        cursor.executemany('''
            INSERT INTO posts (user_id, image_url, location, likes_count, caption)
            VALUES (?, ?, ?, ?, ?)
        ''', posts_data)

        # Seed comments
        comments_data = [
            (1, "rahul_verma", "Wow, that looks stunning! 😍"),
            (1, "anu_style", "Amazing shot Priya!"),
            (2, "priya_sharma", "Looks fun Rahul! Enjoy!"),
            (2, "satish_k", "Awesome vibes bro.")
        ]
        cursor.executemany('''
            INSERT INTO comments (post_id, username, comment_text)
            VALUES (?, ?, ?)
        ''', comments_data)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Instagram Database initialized successfully.")
