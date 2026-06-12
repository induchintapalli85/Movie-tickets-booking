import sqlite3
import os
import uuid
from datetime import datetime, timedelta

DB_FILE = 'bookings.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create movies table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            genre TEXT NOT NULL,
            rating REAL,
            duration TEXT,
            description TEXT,
            poster_url TEXT,
            price_base REAL NOT NULL
        )
    ''')
    
    # Create showtimes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS showtimes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            hall TEXT NOT NULL,
            FOREIGN KEY (movie_id) REFERENCES movies (id)
        )
    ''')
    
    # Create bookings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id TEXT PRIMARY KEY,
            showtime_id INTEGER NOT NULL,
            seats TEXT NOT NULL, -- Comma-separated seat IDs, e.g., "A3,A4"
            total_price REAL NOT NULL,
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (showtime_id) REFERENCES showtimes (id)
        )
    ''')
    
    conn.commit()
    
    # Seed data if empty
    cursor.execute("SELECT COUNT(*) FROM movies")
    if cursor.fetchone()[0] == 0:
        seed_data(conn)
        
    conn.close()

def seed_data(conn):
    cursor = conn.cursor()
    
    # Sample Movies
    movies_data = [
        (
            "Avengers Endgame",
            "Action / Sci-Fi / Adventure",
            8.9,
            "181 mins",
            "After the devastating events of Infinity War, the universe is in ruins. With the help of remaining allies, the Avengers assemble once more to reverse Thanos' actions and restore balance to the universe.",
            "/static/images/avengers.png",
            12.0
        ),
        (
            "Joker",
            "Crime / Drama / Thriller",
            8.5,
            "122 mins",
            "During the 1980s, a failed stand-up comedian clown Arthur Fleck, isolated and mistreated by society, begins a slow descent into madness as he transforms into the criminal mastermind known as the Joker.",
            "/static/images/joker.png",
            10.0
        ),
        (
            "Interstellar",
            "Sci-Fi / Adventure / Drama",
            9.0,
            "169 mins",
            "When Earth becomes uninhabitable in the future, a team of explorers undertakes the most important mission in human history: traveling beyond this galaxy to discover whether mankind has a future among the stars.",
            "/static/images/interstellar.png",
            11.5
        ),
        (
            "Dune: Part Two",
            "Sci-Fi / Action / Drama",
            8.8,
            "166 mins",
            "Paul Atreides unites with Chani and the Fremen while seeking revenge against the conspirators who destroyed his family. Facing a choice between the love of his life and the fate of the universe, he endeavors to prevent a terrible future.",
            "/static/images/dune.png",
            13.0
        )
    ]
    
    cursor.executemany('''
        INSERT INTO movies (title, genre, rating, duration, description, poster_url, price_base)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', movies_data)
    
    conn.commit()
    
    # Get the inserted movie IDs
    cursor.execute("SELECT id FROM movies")
    movie_ids = [row[0] for row in cursor.fetchall()]
    
    # Dynamic showtimes: today, tomorrow, and the day after
    today = datetime.now()
    dates = [
        today.strftime("%Y-%m-%d"),
        (today + timedelta(days=1)).strftime("%Y-%m-%d"),
        (today + timedelta(days=2)).strftime("%Y-%m-%d")
    ]
    
    times = ["10:30 AM", "02:00 PM", "05:30 PM", "09:00 PM"]
    halls = ["Screen 1", "Screen 2", "IMAX Screen"]
    
    showtimes_data = []
    # Seed showtimes for each movie
    for i, movie_id in enumerate(movie_ids):
        # We can seed distinct showtimes and screen assignments for each movie
        for d_idx, date_str in enumerate(dates):
            # Select 2-3 showtimes per date
            for t_idx, time_str in enumerate(times):
                # Distribute slots slightly
                if (i + d_idx + t_idx) % 2 == 0:
                    hall_name = halls[(i + t_idx) % len(halls)]
                    showtimes_data.append((movie_id, date_str, time_str, hall_name))
                    
    cursor.executemany('''
        INSERT INTO showtimes (movie_id, date, time, hall)
        VALUES (?, ?, ?, ?)
    ''', showtimes_data)
    
    conn.commit()

# Helper queries
def get_all_movies():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM movies")
    movies = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return movies

def get_movie_by_id(movie_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM movies WHERE id = ?", (movie_id,))
    movie = cursor.fetchone()
    conn.close()
    return dict(movie) if movie else None

def get_showtimes_for_movie(movie_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM showtimes WHERE movie_id = ? ORDER BY date ASC, time ASC", (movie_id,))
    showtimes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return showtimes

def get_showtime_details(showtime_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.*, m.title, m.poster_url, m.price_base, m.genre
        FROM showtimes s
        JOIN movies m ON s.movie_id = m.id
        WHERE s.id = ?
    ''', (showtime_id,))
    showtime = cursor.fetchone()
    conn.close()
    return dict(showtime) if showtime else None

def get_booked_seats(showtime_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT seats FROM bookings WHERE showtime_id = ?", (showtime_id,))
    bookings = cursor.fetchall()
    conn.close()
    
    booked_seats = []
    for b in bookings:
        seats_list = [s.strip() for s in b['seats'].split(',') if s.strip()]
        booked_seats.extend(seats_list)
    return booked_seats

def create_booking(showtime_id, seats_list, total_price, customer_name, customer_email):
    # Verify that seats are not already booked
    conn = get_db_connection()
    cursor = conn.cursor()
    
    already_booked = get_booked_seats(showtime_id)
    for seat in seats_list:
        if seat in already_booked:
            conn.close()
            raise ValueError(f"Seat {seat} is already booked for this showtime.")
            
    booking_id = str(uuid.uuid4())[:8].upper() # 8-character unique alphanumeric code
    seats_str = ",".join(seats_list)
    
    cursor.execute('''
        INSERT INTO bookings (id, showtime_id, seats, total_price, customer_name, customer_email)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (booking_id, showtime_id, seats_str, total_price, customer_name, customer_email))
    
    conn.commit()
    conn.close()
    return booking_id

def get_booking_details(booking_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT b.*, s.date, s.time, s.hall, m.title as movie_title, m.poster_url
        FROM bookings b
        JOIN showtimes s ON b.showtime_id = s.id
        JOIN movies m ON s.movie_id = m.id
        WHERE b.id = ?
    ''', (booking_id,))
    booking = cursor.fetchone()
    conn.close()
    return dict(booking) if booking else None
