from flask import Flask, jsonify, request
from datetime import datetime
from database import SessionLocal
from models.course import Course
from models.enrollment import Enrollment
from rabbitmq_client import rabbitmq_client

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
        
        # Publish course created event to RabbitMQ
        event_data = {
            "event_type": "course.created",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "course_id": new_course.id,
                "title": new_course.title,
                "description": new_course.description
            }
        }
        try:
            result = rabbitmq_client.publish_event(
                exchange="knowledge_nest_events",
                routing_key="course.created",
                event_data=event_data
            )
            if not result:
                print(f"WARNING: Failed to publish course.created event for course {new_course.id}")
        except Exception as e:
            print(f"ERROR: Exception publishing course.created event: {str(e)}")
        
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

@app.route('/enrollments', methods=['GET'])
def get_user_enrollments():
    user_id = request.args.get('user_id', type=int)
    
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    db = SessionLocal()
    try:
        enrollments = db.query(Enrollment).filter(Enrollment.user_id == user_id).all()
        
        enrollment_list = [{
            "id": enrollment.id,
            "user_id": enrollment.user_id,
            "course_id": enrollment.course_id,
            "enrolled_at": enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else None
        } for enrollment in enrollments]
        
        return jsonify(enrollment_list), 200
        
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
        
        # Publish enrollment event to RabbitMQ
        event_data = {
            "event_type": "course.enrolled",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "enrollment_id": new_enrollment.id,
                "user_id": new_enrollment.user_id,
                "course_id": new_enrollment.course_id,
                "course_title": course.title
            }
        }
        try:
            result = rabbitmq_client.publish_event(
                exchange="knowledge_nest_events",
                routing_key="course.enrolled",
                event_data=event_data
            )
            if not result:
                print(f"WARNING: Failed to publish course.enrolled event for enrollment {new_enrollment.id}")
        except Exception as e:
            print(f"ERROR: Exception publishing course.enrolled event: {str(e)}")
        
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

@app.route('/courses/<int:course_id>/enroll', methods=['DELETE'])
def unenroll_from_course(course_id):
    data = request.get_json() or {}
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    db = SessionLocal()
    try:
        # Check if enrollment exists
        enrollment = db.query(Enrollment).filter(
            Enrollment.user_id == user_id,
            Enrollment.course_id == course_id
        ).first()
        
        if not enrollment:
            return jsonify({"error": "You are not enrolled in this course"}), 404
        
        # Delete enrollment
        db.delete(enrollment)
        db.commit()
        
        return jsonify({
            "message": "Successfully unenrolled from course",
            "course_id": course_id
        }), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
