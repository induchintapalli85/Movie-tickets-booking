from flask import Flask, jsonify, request, render_template
import os
from database import get_db_connection, init_db

app = Flask(__name__)

# Initialize database on startup
init_db()

CURRENT_USER_ID = 1  # Hardcoded session user "chinna_medida"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/feed', methods=['GET'])
def get_feed():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Query all posts with user information
        cursor.execute('''
            SELECT p.id, p.image_url, p.location, p.likes_count, p.caption, p.created_at,
                   u.username, u.full_name, u.profile_pic
            FROM posts p
            JOIN users u ON p.user_id = u.id
            ORDER BY p.created_at DESC
        ''')
        posts_rows = cursor.fetchall()

        feed = []
        for p_row in posts_rows:
            post_id = p_row['id']

            # Query comments for this post
            cursor.execute('''
                SELECT username, comment_text, created_at
                FROM comments
                WHERE post_id = ?
                ORDER BY created_at ASC
            ''', (post_id,))
            comments_rows = cursor.fetchall()
            comments = [{
                'username': c_row['username'],
                'comment_text': c_row['comment_text']
            } for c_row in comments_rows]

            # Check if current user has liked this post
            cursor.execute('''
                SELECT 1 FROM likes
                WHERE post_id = ? AND user_id = ?
            ''', (post_id, CURRENT_USER_ID))
            is_liked = cursor.fetchone() is not None

            feed.append({
                'id': post_id,
                'image_url': p_row['image_url'],
                'location': p_row['location'],
                'likes_count': p_row['likes_count'],
                'caption': p_row['caption'],
                'created_at': p_row['created_at'],
                'username': p_row['username'],
                'full_name': p_row['full_name'],
                'profile_pic': p_row['profile_pic'],
                'comments': comments,
                'is_liked': is_liked
            })

        conn.close()
        return jsonify(feed)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/posts/create', methods=['POST'])
def create_post():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid request payload"}), 400

        image_url = data.get('image_url')
        location = data.get('location', '')
        caption = data.get('caption', '')

        if not image_url:
            return jsonify({"error": "Image URL is required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO posts (user_id, image_url, location, likes_count, caption)
            VALUES (?, ?, ?, 0, ?)
        ''', (CURRENT_USER_ID, image_url, location, caption))
        
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Post shared successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
def toggle_like(post_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if post exists
        cursor.execute("SELECT likes_count FROM posts WHERE id = ?", (post_id,))
        post_row = cursor.fetchone()
        if not post_row:
            conn.close()
            return jsonify({"error": "Post not found"}), 404

        current_likes = post_row['likes_count']

        # Check if already liked
        cursor.execute("SELECT id FROM likes WHERE post_id = ? AND user_id = ?", (post_id, CURRENT_USER_ID))
        like_row = cursor.fetchone()

        if like_row:
            # Unlike: Delete like row, decrement likes_count
            cursor.execute("DELETE FROM likes WHERE post_id = ? AND user_id = ?", (post_id, CURRENT_USER_ID))
            new_likes = max(0, current_likes - 1)
            cursor.execute("UPDATE posts SET likes_count = ? WHERE id = ?", (new_likes, post_id))
            liked = False
        else:
            # Like: Insert like row, increment likes_count
            cursor.execute("INSERT INTO likes (post_id, user_id) VALUES (?, ?)", (post_id, CURRENT_USER_ID))
            new_likes = current_likes + 1
            cursor.execute("UPDATE posts SET likes_count = ? WHERE id = ?", (new_likes, post_id))
            liked = True

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "liked": liked,
            "likes_count": new_likes
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/posts/<int:post_id>/comment', methods=['POST'])
def add_comment(post_id):
    try:
        data = request.json
        if not data or not data.get('comment_text'):
            return jsonify({"error": "Comment text is required"}), 400

        comment_text = data.get('comment_text')

        conn = get_db_connection()
        cursor = conn.cursor()

        # Verify post exists
        cursor.execute("SELECT id FROM posts WHERE id = ?", (post_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({"error": "Post not found"}), 404

        # Get current user's username
        cursor.execute("SELECT username FROM users WHERE id = ?", (CURRENT_USER_ID,))
        current_username = cursor.fetchone()['username']

        cursor.execute('''
            INSERT INTO comments (post_id, username, comment_text)
            VALUES (?, ?, ?)
        ''', (post_id, current_username, comment_text))

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "comment": {
                "username": current_username,
                "comment_text": comment_text
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stories', methods=['GET'])
def get_stories():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.id, s.image_url, u.username, u.profile_pic
            FROM stories s
            JOIN users u ON s.user_id = u.id
        ''')
        stories_rows = cursor.fetchall()
        conn.close()

        stories = [{
            'id': row['id'],
            'image_url': row['image_url'],
            'username': row['username'],
            'profile_pic': row['profile_pic']
        } for row in stories_rows]

        return jsonify(stories)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/suggestions', methods=['GET'])
def get_suggestions():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Suggested users are other users who we don't necessarily follow yet, but let's just show all other users
        cursor.execute('''
            SELECT id, username, full_name, profile_pic, is_following
            FROM users
            WHERE id != ?
            LIMIT 5
        ''', (CURRENT_USER_ID,))
        suggestions_rows = cursor.fetchall()
        conn.close()

        suggestions = [{
            'id': row['id'],
            'username': row['username'],
            'full_name': row['full_name'],
            'profile_pic': row['profile_pic'],
            'is_following': bool(row['is_following'])
        } for row in suggestions_rows]

        return jsonify(suggestions)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/users/<int:user_id>/follow', methods=['POST'])
def toggle_follow(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute("SELECT is_following FROM users WHERE id = ?", (user_id,))
        user_row = cursor.fetchone()
        if not user_row:
            conn.close()
            return jsonify({"error": "User not found"}), 404

        current_follow = user_row['is_following']
        new_follow = 1 if current_follow == 0 else 0

        cursor.execute("UPDATE users SET is_following = ? WHERE id = ?", (new_follow, user_id))
        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "is_following": bool(new_follow)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
