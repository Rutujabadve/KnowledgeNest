from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import requests
import jwt
from functools import wraps

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET', 'dev-secret-key-change-in-production')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            request.user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        
        return f(*args, **kwargs)
    
    return decorated

# Service URLs
AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://localhost:5001')
COURSE_SERVICE_URL = os.getenv('COURSE_SERVICE_URL', 'http://localhost:5002')
REVIEW_SERVICE_URL = os.getenv('REVIEW_SERVICE_URL', 'http://localhost:5003')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "api_gateway"}), 200

# Auth routes - proxy to Auth Service
@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        response = requests.post(
            f'{AUTH_SERVICE_URL}/register',
            json=request.get_json(),
            headers={'Content-Type': 'application/json'}
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        response = requests.post(
            f'{AUTH_SERVICE_URL}/login',
            json=request.get_json(),
            headers={'Content-Type': 'application/json'}
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Course routes - proxy to Course Service
@app.route('/api/courses', methods=['GET', 'POST'])
def courses():
    try:
        if request.method == 'GET':
            response = requests.get(f'{COURSE_SERVICE_URL}/courses')
        else:  # POST
            response = requests.post(
                f'{COURSE_SERVICE_URL}/courses',
                json=request.get_json(),
                headers={'Content-Type': 'application/json'}
            )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/courses/<int:course_id>/enroll', methods=['POST'])
@token_required
def enroll(course_id):
    try:
        # Add user_id from JWT to request body
        data = request.get_json() or {}
        data['user_id'] = request.user_id
        
        response = requests.post(
            f'{COURSE_SERVICE_URL}/courses/{course_id}/enroll',
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Review routes - proxy to Review Service
@app.route('/api/courses/<int:course_id>/reviews', methods=['POST'])
@token_required
def create_review(course_id):
    try:
        # Add user_id from JWT to request body
        data = request.get_json() or {}
        data['user_id'] = request.user_id
        
        response = requests.post(
            f'{REVIEW_SERVICE_URL}/courses/{course_id}/reviews',
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
