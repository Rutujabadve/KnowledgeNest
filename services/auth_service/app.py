from flask import Flask, jsonify, request
import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from database import SessionLocal
from models.user import User

app = Flask(__name__)
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
            current_user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        
        return f(current_user_id, *args, **kwargs)
    
    return decorated

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password required"}), 400
    
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == data['email']).first()
        if existing_user:
            return jsonify({"error": "User already exists"}), 409
        
        # Hash password with bcrypt
        password_bytes = data['password'].encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt)
        
        # Create new user
        new_user = User(
            email=data['email'],
            password_hash=hashed_password.decode('utf-8'),
            name=data.get('name', '')
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return jsonify({
            "id": new_user.id,
            "email": new_user.email,
            "name": new_user.name
        }), 201
        
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password required"}), 400
    
    db = SessionLocal()
    try:
        # Find user by email
        user = db.query(User).filter(User.email == data['email']).first()
        if not user:
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Verify password
        password_bytes = data['password'].encode('utf-8')
        stored_hash = user.password_hash.encode('utf-8')
        
        if not bcrypt.checkpw(password_bytes, stored_hash):
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Generate JWT token
        payload = {
            'user_id': user.id,
            'email': user.email,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            "access_token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name
            }
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@app.route('/users/<int:user_id>', methods=['GET'])
@token_required
def get_user(current_user_id, user_id):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify({
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
