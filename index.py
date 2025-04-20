import logging
import os
from functools import wraps
from typing import Dict, Tuple, Any, Generator
from dotenv import load_dotenv
from flask import Flask, jsonify, request, Response, abort
import ollama
from werkzeug.exceptions import HTTPException

# Load configuration
load_dotenv()
CONFIG = {
    "FLASK_HOST": os.getenv("FLASK_HOST", "0.0.0.0"),
    "FLASK_PORT": int(os.getenv("FLASK_PORT", "5000")),
    "FLASK_DEBUG": os.getenv("FLASK_DEBUG", "false").lower() == "true",
    "OLLAMA_HOST": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
    "MODEL_NAME": os.getenv("MODEL_NAME", "deepseek-r1:7b"),
    "API_KEY": os.getenv("API_KEY", ""),
    "RATE_LIMIT": int(os.getenv("RATE_LIMIT", "100")),
}

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

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if CONFIG["API_KEY"] and request.headers.get('X-API-KEY') != CONFIG["API_KEY"]:
            abort(401, "Invalid API Key")
        return f(*args, **kwargs)
    return decorated

def validate_chat_input(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        data = request.get_json()
        if not data:
            abort(400, "Request body must be JSON")
        if "messages" not in data or not isinstance(data["messages"], list):
            abort(400, "Must include 'messages' array")
        return f(*args, **kwargs)
    return wrapper

@app.errorhandler(HTTPException)
def handle_http_error(e):
    return jsonify({
        "error": e.name,
        "code": e.code,
        "message": e.description
    }), e.code

@app.route("/chat", methods=["POST"])
@require_api_key
@validate_chat_input
def chat_handler():
    data = request.get_json()
    stream = data.get("stream", False)
    
    try:
        if stream:
            def generate():
                for chunk in ollama_client.chat(
                    model=CONFIG["MODEL_NAME"],
                    messages=data["messages"],
                    stream=True
                ):
                    yield f"{chunk['message']['content']}"
            
            return Response(generate(), mimetype="text/event-stream")
        else:
            response = ollama_client.chat(
                model=CONFIG["MODEL_NAME"],
                messages=data["messages"],
                stream=False
            )
            return jsonify({
                "model": CONFIG["MODEL_NAME"],
                "response": response["message"]["content"],
                "processing_time": response.get("processing_time", 0)
            })
            
    except Exception as e:
        logger.error("Processing error: %s", str(e))
        abort(500, "AI processing failed")

@app.route("/health", methods=["GET"])
def health_check():
    try:
        ollama_client.list_models()
        return jsonify({
            "status": "healthy",
            "model": CONFIG["MODEL_NAME"],
            "ollama": "connected"
        })
    except Exception as e:
        return jsonify({
            "status": "degraded",
            "error": str(e)
        }), 503

if __name__ == "__main__":
    app.run(
        host=CONFIG["FLASK_HOST"],
        port=CONFIG["FLASK_PORT"],
        debug=CONFIG["FLASK_DEBUG"]
    )