from flask import Flask, jsonify
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET', 'dev-secret-key-change-in-production')

# Service URLs
AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://localhost:5001')
COURSE_SERVICE_URL = os.getenv('COURSE_SERVICE_URL', 'http://localhost:5002')
REVIEW_SERVICE_URL = os.getenv('REVIEW_SERVICE_URL', 'http://localhost:5003')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "api_gateway"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
