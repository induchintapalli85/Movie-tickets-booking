from flask import Flask, request, jsonify, send_from_directory
import os
import database

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Initialize DB on startup
database.init_db()

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/movies', methods=['GET'])
def get_movies():
    try:
        movies = database.get_all_movies()
        return jsonify(movies)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/movies/<int:movie_id>/showtimes', methods=['GET'])
def get_showtimes(movie_id):
    try:
        showtimes = database.get_showtimes_for_movie(movie_id)
        return jsonify(showtimes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/showtimes/<int:showtime_id>/seats', methods=['GET'])
def get_seats(showtime_id):
    try:
        showtime = database.get_showtime_details(showtime_id)
        if not showtime:
            return jsonify({"error": "Showtime not found"}), 404
        
        booked_seats = database.get_booked_seats(showtime_id)
        
        # We can also return some metadata about the layout, like price base
        return jsonify({
            "showtime_id": showtime_id,
            "hall": showtime['hall'],
            "price_base": showtime['price_base'],
            "booked_seats": booked_seats
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/bookings', methods=['POST'])
def book_tickets():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        showtime_id = data.get('showtime_id')
        seats = data.get('seats')
        total_price = data.get('total_price')
        customer_name = data.get('customer_name')
        customer_email = data.get('customer_email')
        
        if not all([showtime_id, seats, total_price, customer_name, customer_email]):
            return jsonify({"error": "Missing required fields"}), 400
            
        if not isinstance(seats, list) or len(seats) == 0:
            return jsonify({"error": "Seats must be a non-empty list"}), 400
            
        # Create booking in DB
        booking_id = database.create_booking(
            showtime_id=showtime_id,
            seats_list=seats,
            total_price=total_price,
            customer_name=customer_name,
            customer_email=customer_email
        )
        
        return jsonify({
            "success": True,
            "booking_id": booking_id
        }), 201
        
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/bookings/<booking_id>', methods=['GET'])
def get_booking(booking_id):
    try:
        booking = database.get_booking_details(booking_id)
        if not booking:
            return jsonify({"error": "Booking not found"}), 404
            
        return jsonify(booking)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Running on port 5000 in debug mode
    app.run(debug=True, host='0.0.0.0', port=5000)
