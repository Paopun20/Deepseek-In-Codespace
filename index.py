"""
AI Chat Service with Flask

Enhanced Features:
- Configurable environment variables
- Input validation with error handling
- Comprehensive HTTP error handlers
- Dependency checks in health endpoint
- Structured logging
"""

import logging
import os
from functools import wraps
from typing import Dict, Tuple, Any

from dotenv import load_dotenv
from flask import Flask, jsonify, request, abort
import ollama
from werkzeug.exceptions import HTTPException

# --------------------------
#      CONFIGURATION
# --------------------------

load_dotenv()

# Application configuration
CONFIG = {
    "FLASK_HOST": os.getenv("FLASK_HOST", "0.0.0.0"),
    "FLASK_PORT": int(os.getenv("FLASK_PORT", "6969")),
    "FLASK_DEBUG": os.getenv("FLASK_DEBUG", "false").lower() == "true",
    "OLLAMA_HOST": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
    "MODEL_NAME": os.getenv("MODEL_NAME", "deepseek-r1:7b"),
}

# Initialize Flask app
app = Flask(__name__)
app.config.update(CONFIG)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if CONFIG["FLASK_DEBUG"] else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("AI Chat Service")

# Initialize Ollama client
try:
    ollama_client = ollama.Client(host=CONFIG["OLLAMA_HOST"])
    logger.info("Connected to Ollama at %s", CONFIG["OLLAMA_HOST"])
except Exception as e:
    logger.error("Failed to initialize Ollama client: %s", str(e))
    raise RuntimeError("Ollama connection failed") from e

# --------------------------
#      HELPER FUNCTIONS
# --------------------------

def validate_chat_input(func):
    """Decorator for input validation"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        data = request.get_json()
        if not data or "input" not in data:
            abort(400, "Missing 'input' field in request body")
        return func(*args, **kwargs)
    return wrapper

# --------------------------
#      ERROR HANDLERS
# --------------------------

@app.errorhandler(HTTPException)
def handle_http_error(e):
    """JSON-formatted HTTP errors"""
    logger.warning("HTTP error %d: %s", e.code, e.description)
    return jsonify({
        "error": e.name,
        "code": e.code,
        "message": e.description
    }), e.code

@app.errorhandler(Exception)
def handle_unexpected_error(e):
    """Generic error handler"""
    logger.exception("Unexpected error occurred")
    return jsonify({
        "error": "Internal Server Error",
        "code": 500,
        "message": "An unexpected error occurred"
    }), 500

# --------------------------
#      ROUTES
# --------------------------

@app.route("/chat", methods=["POST"])
@validate_chat_input
def chat_handler() -> Tuple[Dict[str, Any], int]:
    """Handle chat requests with AI processing"""
    try:
        data = request.get_json()
        response = ollama_client.chat(
            model=CONFIG["MODEL_NAME"],
            messages=[{"role": "user", "content": data["input"]}],
            stream=False
        )
        return jsonify({
            "response": response["message"]["content"],
            "model": CONFIG["MODEL_NAME"],
            "processing_time": response.get("processing_time", 0)
        }), 200
    
    except ollama.ResponseError as e:
        logger.error("Ollama API error: %s", str(e))
        return jsonify({
            "error": "AI Service Error",
            "code": 502,
            "message": str(e.error)
        }), 502
        
    except ollama.RequestError as e:
        logger.error("Ollama request error: %s", str(e))
        return jsonify({
            "error": "AI Service Error",
            "code": 502,
            "message": str(e.error)
        }), 502
        
    except ValueError as e:
        logger.error("Invalid input: %s", str(e))
        return jsonify({
            "error": "Bad Request",
            "code": 400,
            "message": str(e)
        }), 400
        
    except Exception as e:
        logger.exception("Unexpected error during chat processing")
        return jsonify({
            "error": "Internal Server Error",
            "code": 500,
            "message": "An unexpected error occurred during chat processing"
        }), 500
        
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
        return jsonify({
            "error": "Service Interrupted",
            "code": 500,
            "message": "Service interrupted by user"
        }), 500
        
    except ConnectionError:
        logger.error("Connection to Ollama failed")
        return jsonify({
            "error": "Service Unavailable",
            "code": 503,
            "message": "AI service is currently unavailable"
        }), 503

@app.route("/health", methods=["GET", "POST"])
def health_check() -> Tuple[Dict[str, Any], int]:
    """Service health endpoint with dependency checks"""
    status = {"status": "healthy", "errors": []}
    
    # Check Ollama connection
    try:
        ollama_client.list_models()
    except Exception as e:
        status["status"] = "degraded"
        status["errors"].append(f"Ollama connection failed: {str(e)}")
    
    return jsonify({
        "status": status["status"],
        "version": "1.0.0",
        "dependencies": {
            "ollama": "operational" if not status["errors"] else "degraded"
        },
        "details": status["errors"] if status["errors"] else "All systems operational"
    }), 200 if status["status"] == "healthy" else 503

# --------------------------
#      MAIN EXECUTION
# --------------------------

if __name__ == "__main__":
    try:
        logger.info("Starting AI Chat Service on %s:%d", 
                   CONFIG["FLASK_HOST"], CONFIG["FLASK_PORT"])
        app.run(
            host=CONFIG["FLASK_HOST"],
            port=CONFIG["FLASK_PORT"],
            debug=CONFIG["FLASK_DEBUG"],
            use_reloader=False
        )
    except Exception as e:
        logger.critical("Failed to start service: %s", str(e))
        raise