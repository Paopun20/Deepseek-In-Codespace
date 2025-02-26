from flask import Flask, request, jsonify, redirect
from ollama import chat
import logging
import os
from dotenv import load_dotenv  # For environment variables
from functools import wraps

# Load environment variables from .env file
load_dotenv()

# === 🔧 CONFIGURATION SETUP ===
class Config:
    AI_MODEL = os.getenv('AI_MODEL', 'deepseek-r1')
    PORT = int(os.getenv('PORT', 5000))
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG' if DEBUG_MODE else 'INFO')
    MAX_INPUT_LENGTH = int(os.getenv('MAX_INPUT_LENGTH', 1000))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '').split(',')
    RATE_LIMIT = os.getenv('RATE_LIMIT', '100 per day;50 per hour')

# === 📝 LOGGING CONFIGURATION ===
logging.basicConfig(
    level=Config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# === 🚀 FLASK APP INITIALIZATION ===
app = Flask(__name__)
app.config.from_object(Config)

# === 🚦 RATE LIMITING ===
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[app.config['RATE_LIMIT']]
)

# === 🛡️ DECORATORS ===
def validate_json(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not request.is_json:
            logger.warning("Non-JSON request received")
            return json_error("Unsupported Media Type: JSON required", 415)
        try:
            request.get_json()
        except Exception as e:
            logger.warning(f"Invalid JSON received: {str(e)}")
            return json_error("Invalid JSON format", 400)
        return f(*args, **kwargs)
    return wrapper

def validate_input(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        data = request.get_json()
        if 'input' not in data:
            return json_error("Missing 'input' field", 400)
        
        if len(data) > 1:
            return json_error("Unexpected fields in request", 400)
        
        user_input = data['input']
        if not isinstance(user_input, str) or not user_input.strip():
            return json_error("Input must be a non-empty string", 422)
        
        if len(user_input) > app.config['MAX_INPUT_LENGTH']:
            return json_error(f"Input exceeds maximum length of {app.config['MAX_INPUT_LENGTH']} characters", 413)
        
        return f(*args, **kwargs)
    return wrapper

# === 🛠️ HELPER FUNCTIONS ===
def json_error(message, status_code):
    logger.error(f"Error {status_code}: {message}")
    return jsonify({
        "status": "error",
        "message": message,
        "code": status_code
    }), status_code

def sanitize_input(text: str) -> str:
    """Basic sanitization to prevent simple injection attacks"""
    return text.replace('<', '&lt;').replace('>', '&gt;').strip()

def generate_ai_response(prompt):
    try:
        response = chat(
            model=app.config['AI_MODEL'],
            messages=[{'role': 'user', 'content': prompt}],
            stream=False,
            options={'timeout': app.config['REQUEST_TIMEOUT']}
        )
        
        if not response or not isinstance(response, dict) or 'message' not in response:
            raise ValueError("Unexpected response structure from AI model")

        message = response.get('message', {})
        ai_content = message.get('content', '')

        if not ai_content:
            raise ValueError("AI model returned an empty response")
        return ai_content
    
    except Exception as e:
        logger.error(f"AI Service Error: {str(e)}", exc_info=app.config['DEBUG_MODE'])
        raise

# === 🎯 ROUTES ===
@app.route('/chat', methods=['POST'])
@validate_json
@validate_input
@limiter.limit(app.config['RATE_LIMIT'])
def chat_handler():
    data = request.get_json()
    user_input = sanitize_input(data['input'])
    logger.info(f"Processing request: {user_input[:50]}...")

    try:
        ai_response = generate_ai_response(user_input)
        logger.debug(f"Generated response: {ai_response[:100]}...")
        
        return jsonify({
            "status": "success",
            "data": {
                "response": ai_response
            }
        })
        
    except Exception as e:
        return json_error(f"AI processing failed: {str(e)}", 500)

@app.route('/health')
def health_check():
    return jsonify({
        "status": "success",
        "message": "Service is operational",
        "version": "1.0.0"
    })

# === ❌ ERROR HANDLERS ===
@app.errorhandler(400)
def bad_request(error):
    return json_error("Bad Request: Invalid JSON", 400)

@app.errorhandler(404)
def not_found(error):
    return json_error("Endpoint not found", 404)

@app.errorhandler(405)
def method_not_allowed(error):
    return json_error("Method not allowed", 405)

@app.errorhandler(429)
def ratelimit_handler(e):
    return json_error("Rate limit exceeded", 429)

# === 🏃 START APPLICATION ===
if __name__ == '__main__':
    logger.info(f"Starting server in {'DEBUG' if app.config['DEBUG_MODE'] else 'PRODUCTION'} mode")
    logger.info(f"Using AI model: {app.config['AI_MODEL']}")
    logger.info(f"CORS allowed origins: {app.config['CORS_ORIGINS'] or 'All'}")
    app.run(
        host='0.0.0.0',
        port=app.config['PORT'],
        debug=app.config['DEBUG_MODE']
    )