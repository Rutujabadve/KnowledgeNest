from flask import Flask, jsonify, request
from database import SessionLocal
from models.user import User

app = Flask(__name__)

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
        
        # Create new user (no hashing yet - will add in T2.03)
        new_user = User(
            email=data['email'],
            password_hash=data['password'],  # Storing plaintext for now
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
