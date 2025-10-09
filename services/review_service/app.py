from flask import Flask, jsonify, request
from database import SessionLocal
from models.review import Review

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/courses/<int:course_id>/reviews', methods=['POST'])
def create_review(course_id):
    data = request.get_json()
    
    if not data or not data.get('user_id') or not data.get('rating'):
        return jsonify({"error": "User ID and rating are required"}), 400
    
    # Validate rating
    rating = data.get('rating')
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({"error": "Rating must be between 1 and 5"}), 400
    
    db = SessionLocal()
    try:
        # Check if user already reviewed this course
        existing_review = db.query(Review).filter(
            Review.user_id == data['user_id'],
            Review.course_id == course_id
        ).first()
        
        if existing_review:
            return jsonify({"error": "You have already reviewed this course"}), 409
        
        # Create review
        new_review = Review(
            user_id=data['user_id'],
            course_id=course_id,
            rating=rating,
            comment=data.get('comment', '')
        )
        
        db.add(new_review)
        db.commit()
        db.refresh(new_review)
        
        return jsonify({
            "id": new_review.id,
            "user_id": new_review.user_id,
            "course_id": new_review.course_id,
            "rating": new_review.rating,
            "comment": new_review.comment,
            "created_at": new_review.created_at.isoformat() if new_review.created_at else None
        }), 201
        
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@app.route('/courses/<int:course_id>/reviews', methods=['GET'])
def get_reviews(course_id):
    db = SessionLocal()
    try:
        reviews = db.query(Review).filter(Review.course_id == course_id).all()
        
        reviews_list = [{
            "id": review.id,
            "user_id": review.user_id,
            "course_id": review.course_id,
            "rating": review.rating,
            "comment": review.comment,
            "created_at": review.created_at.isoformat() if review.created_at else None
        } for review in reviews]
        
        return jsonify(reviews_list), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
