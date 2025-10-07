from flask import Flask, jsonify, request
from database import SessionLocal
from models.course import Course
from models.enrollment import Enrollment

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/courses', methods=['POST'])
def create_course():
    data = request.get_json()
    
    if not data or not data.get('title'):
        return jsonify({"error": "Title is required"}), 400
    
    db = SessionLocal()
    try:
        new_course = Course(
            title=data['title'],
            description=data.get('description', ''),
            content_url=data.get('content_url', '')
        )
        
        db.add(new_course)
        db.commit()
        db.refresh(new_course)
        
        return jsonify({
            "id": new_course.id,
            "title": new_course.title,
            "description": new_course.description,
            "content_url": new_course.content_url,
            "created_at": new_course.created_at.isoformat() if new_course.created_at else None
        }), 201
        
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@app.route('/courses', methods=['GET'])
def list_courses():
    db = SessionLocal()
    try:
        courses = db.query(Course).all()
        
        courses_list = [{
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "content_url": course.content_url,
            "created_at": course.created_at.isoformat() if course.created_at else None
        } for course in courses]
        
        return jsonify(courses_list), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@app.route('/courses/<int:course_id>/enroll', methods=['POST'])
def enroll_in_course(course_id):
    data = request.get_json()
    
    if not data or not data.get('user_id'):
        return jsonify({"error": "User ID is required"}), 400
    
    db = SessionLocal()
    try:
        # Check if course exists
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            return jsonify({"error": "Course not found"}), 404
        
        # Check if already enrolled
        existing_enrollment = db.query(Enrollment).filter(
            Enrollment.user_id == data['user_id'],
            Enrollment.course_id == course_id
        ).first()
        
        if existing_enrollment:
            return jsonify({"error": "Already enrolled in this course"}), 409
        
        # Create enrollment
        new_enrollment = Enrollment(
            user_id=data['user_id'],
            course_id=course_id
        )
        
        db.add(new_enrollment)
        db.commit()
        db.refresh(new_enrollment)
        
        return jsonify({
            "id": new_enrollment.id,
            "user_id": new_enrollment.user_id,
            "course_id": new_enrollment.course_id,
            "enrolled_at": new_enrollment.enrolled_at.isoformat() if new_enrollment.enrolled_at else None
        }), 201
        
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
