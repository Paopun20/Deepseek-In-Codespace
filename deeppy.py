"""
AI Chat Service with Flask

Features:
- REST API endpoint for AI-powered chat
- Rate limiting and input validation
- Comprehensive error handling
- Environment-based configuration
- Health check endpoint
"""

import logging
import os
from functools import wraps
from typing import Dict, Tuple, Any

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from ollama import chat

# --------------------------
#      CONFIGURATION
# --------------------------

load_dotenv()

class Config:
    """
    Application configuration with environment variables
    """
    AI_MODEL = os.getenv("AI_MODEL", "deepseek-r1")
    PORT = int(os.getenv("PORT", "5000"))
    DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG" if DEBUG_MODE else "INFO")
    MAX_INPUT_LENGTH = int(os.getenv("MAX_INPUT_LENGTH", "1000"))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",")
    RATE_LIMIT = os.getenv("RATE_LIMIT", "100/day;50/hour").split(";")


# --------------------------
#      INITIALIZATION
# --------------------------

# Configure logging
logging.basicConfig(
    level=Config.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("service.log")
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS
CORS(app, origins=app.config["CORS_ORIGINS"])

# Rate limiting configuration
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=app.config["RATE_LIMIT"]
)

# --------------------------
#      DECORATORS
# --------------------------

def validate_json(func):
    """Ensure requests contain valid JSON payload"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not request.is_json:
            logger.warning("Non-JSON request received")
            return json_error("JSON payload required", 415)
            
        try:
            request.get_json()
        except Exception as e:
            logger.warning(f"Invalid JSON: {str(e)}")
            return json_error("Malformed JSON", 400)
            
        return func(*args, **kwargs)
    return wrapper


def validate_input(func):
    """Validate chat input structure and content"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        data = request.get_json()
        
        if "input" not in data:
            return json_error("Missing 'input' field", 400)
            
        if len(data) > 1:
            return json_error("Unexpected fields in payload", 400)
            
        user_input = data["input"]
        if not isinstance(user_input, str) or not user_input.strip():
            return json_error("Input must be non-empty string", 422)
            
        if len(user_input) > app.config["MAX_INPUT_LENGTH"]:
            return json_error(
                f"Input exceeds {app.config['MAX_INPUT_LENGTH']} characters", 
                413
            )
            
        return func(*args, **kwargs)
    return wrapper

# --------------------------
#      HELPER FUNCTIONS
# --------------------------

def json_error(message: str, status_code: int) -> Tuple[Dict[str, Any], int]:
    """Standard error response formatter"""
    logger.error(f"Error {status_code}: {message}")
    return jsonify({
        "status": "error",
        "message": message,
        "code": status_code
    }), status_code


def sanitize_input(text: str) -> str:
    """Basic input sanitization to prevent XSS attacks"""
    return text.replace("<", "&lt;").replace(">", "&gt;").strip()


def generate_ai_response(prompt: str) -> str:
    """Generate AI response using configured model"""
    try:
        response = chat(
            model=app.config["AI_MODEL"],
            messages=[{"role": "user", "content": prompt}],
            stream=False,
            options={"timeout": app.config["REQUEST_TIMEOUT"]}
        )
        
        if not response or "message" not in response:
            raise ValueError("Invalid response structure from AI model")
            
        return response["message"].get("content", "")
        
    except Exception as e:
        logger.exception("AI service failure")
        raise RuntimeError("AI processing failed") from e

# --------------------------
#      ROUTES
# --------------------------

@app.route("/chat", methods=["POST"])
@validate_json
@validate_input
@limiter.limit(app.config["RATE_LIMIT"])
def chat_handler() -> Tuple[Dict[str, Any], int]:
    """Handle chat requests"""
    data = request.get_json()
    user_input = sanitize_input(data["input"])
    
    logger.info(f"Processing request: {user_input[:50]}...")
    
    try:
        ai_response = generate_ai_response(user_input)
        logger.debug(f"Generated response: {ai_response[:100]}...")
        
        return jsonify({
            "status": "success",
            "data": {"response": ai_response}
        })
        
    except Exception as e:
        return json_error(str(e), 500)


@app.route("/health")
def health_check() -> Tuple[Dict[str, Any], int]:
    """Service health endpoint"""
    return jsonify({
        "status": "success",
        "message": "Service operational",
        "version": "1.0.0",
        "dependencies": {
            "ai_model": app.config["AI_MODEL"],
            "status": "connected"
        }
    })

# --------------------------
#      ERROR HANDLERS
# --------------------------

@app.errorhandler(404)
def not_found_error(e) -> Tuple[Dict[str, Any], int]:
    return json_error("Endpoint not found", 404)


@app.errorhandler(429)
def rate_limit_error(e) -> Tuple[Dict[str, Any], int]:
    return json_error("Rate limit exceeded", 429)


@app.errorhandler(Exception)
def handle_unexpected_error(e) -> Tuple[Dict[str, Any], int]:
    logger.exception("Unexpected error occurred")
    return json_error("Internal server error", 500)

# --------------------------
#      MAIN EXECUTION
# --------------------------

if __name__ == "__main__":
    logger.info("\n" + "="*40)
    logger.info(f"{' AI Chat Service ':#^40}")
    logger.info("="*40)
    logger.info(f"Environment: {'Development' if app.config['DEBUG_MODE'] else 'Production'}")
    logger.info(f"AI Model: {app.config['AI_MODEL']}")
    logger.info(f"CORS Origins: {app.config['CORS_ORIGINS'] or 'All'}")
    logger.info(f"Rate Limits: {app.config['RATE_LIMIT']}")
    
    app.run(
        host="0.0.0.0",
        port=app.config["PORT"],
        debug=app.config["DEBUG_MODE"],
        use_reloader=False
    )