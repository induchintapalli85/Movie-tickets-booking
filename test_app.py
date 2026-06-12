import sys
import os
import json
import unittest

# Add project root to path
sys.path.append(r"c:\Users\HP\OneDrive\Attachments\ticket booking")

import app
import database

class MovieBookingTestCase(unittest.TestCase):
    def setUp(self):
        # We will use a separate test database file or just use the default bookings.db for testing
        # To avoid polluting database, let's back it up or just use a testing DB.
        # Let's set the db file to a testing one.
        database.DB_FILE = 'test_bookings.db'
        
        # Clean up database if exists
        if os.path.exists(database.DB_FILE):
            os.remove(database.DB_FILE)
            
        database.init_db()
        self.client = app.app.test_client()

    def tearDown(self):
        # Clean up test database
        if os.path.exists(database.DB_FILE):
            os.remove(database.DB_FILE)

    def test_api_flow(self):
        print("\n--- Starting API Integration Tests ---")
        
        # 1. Fetch movies
        response = self.client.get('/api/movies')
        self.assertEqual(response.status_code, 200)
        movies = json.loads(response.data)
        self.assertTrue(isinstance(movies, list))
        self.assertGreater(len(movies), 0)
        print(f"[OK] GET /api/movies returned {len(movies)} movies.")

        first_movie = movies[0]
        movie_id = first_movie['id']
        self.assertIn('title', first_movie)
        self.assertIn('price_base', first_movie)

        # 2. Fetch showtimes for first movie
        response = self.client.get(f'/api/movies/{movie_id}/showtimes')
        self.assertEqual(response.status_code, 200)
        showtimes = json.loads(response.data)
        self.assertTrue(isinstance(showtimes, list))
        self.assertGreater(len(showtimes), 0)
        print(f"[OK] GET /api/movies/{movie_id}/showtimes returned {len(showtimes)} showtimes.")

        showtime_id = showtimes[0]['id']

        # 3. Fetch seat occupancy (should be empty initially)
        response = self.client.get(f'/api/showtimes/{showtime_id}/seats')
        self.assertEqual(response.status_code, 200)
        seats_data = json.loads(response.data)
        self.assertEqual(seats_data['showtime_id'], showtime_id)
        self.assertEqual(len(seats_data['booked_seats']), 0)
        print("[OK] GET /api/showtimes/1/seats returned empty booked_seats list.")

        # 4. Make a booking
        booking_payload = {
            "showtime_id": showtime_id,
            "seats": ["C3", "C4"],
            "total_price": 30.0,
            "customer_name": "Test User",
            "customer_email": "test@example.com"
        }
        response = self.client.post('/api/bookings', 
                                   data=json.dumps(booking_payload),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 201)
        booking_res = json.loads(response.data)
        self.assertTrue(booking_res['success'])
        booking_id = booking_res['booking_id']
        self.assertIsNotNone(booking_id)
        print(f"[OK] POST /api/bookings successfully created booking: {booking_id}")

        # 5. Fetch booking receipt details
        response = self.client.get(f'/api/bookings/{booking_id}')
        self.assertEqual(response.status_code, 200)
        booking_details = json.loads(response.data)
        self.assertEqual(booking_details['id'], booking_id)
        self.assertEqual(booking_details['seats'], "C3,C4")
        self.assertEqual(booking_details['customer_name'], "Test User")
        print("[OK] GET /api/bookings/ID successfully fetched accurate receipt details.")

        # 6. Fetch seat occupancy again (should now contain C3 and C4)
        response = self.client.get(f'/api/showtimes/{showtime_id}/seats')
        self.assertEqual(response.status_code, 200)
        seats_data = json.loads(response.data)
        self.assertIn("C3", seats_data['booked_seats'])
        self.assertIn("C4", seats_data['booked_seats'])
        self.assertEqual(len(seats_data['booked_seats']), 2)
        print("[OK] GET /api/showtimes/1/seats verified seats C3 and C4 are locked/occupied.")

        # 7. Attempt double booking on C3 (should fail with 409 conflict)
        duplicate_payload = {
            "showtime_id": showtime_id,
            "seats": ["C3", "D1"],
            "total_price": 25.0,
            "customer_name": "Another User",
            "customer_email": "another@example.com"
        }
        response = self.client.post('/api/bookings', 
                                   data=json.dumps(duplicate_payload),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 409)
        duplicate_res = json.loads(response.data)
        self.assertIn("already booked", duplicate_res['error'])
        print("[OK] POST /api/bookings properly prevented double booking with a 409 Conflict.")
        print("--- All Tests Passed Successfully ---\n")

if __name__ == '__main__':
    unittest.main()
