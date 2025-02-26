#!/bin/bash

set -euo pipefail

# Color codes for formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
MODEL_NAME="deepseek-r1:7b"  # Model to install
OLLAMA_PORT=11434            # Port for Ollama
LOG_FILE="codespaces_setup.log"

# Codespaces-specific adjustments
CODESPACES=${CODESPACES:-"false"}  # Automatically set in GitHub Codespaces

# Initialize log file
echo "Codespaces setup started at $(date)" > "$LOG_FILE"

# Function to handle errors
handle_error() {
    local line="$1"
    local message="$2"
    echo -e "${RED}Error occurred on line $line: $message${NC}" | tee -a "$LOG_FILE"
    exit 1
}

trap 'handle_error $LINENO "$BASH_COMMAND"' ERR

# Function to check command availability
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install system dependencies
install_packages() {
    echo -e "${YELLOW}Installing system dependencies...${NC}"
    sudo apt-get update -y >> "$LOG_FILE" 2>&1
    sudo apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        curl \
        >> "$LOG_FILE" 2>&1
}

# Install Python dependencies globally
install_python_dependencies() {
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    pip3 install --user flask flask-cors python-dotenv ollama flask_limiter >> "$LOG_FILE" 2>&1
}

# Install Ollama
install_ollama() {
    echo -e "${YELLOW}Installing Ollama...${NC}"
    curl -fsSL https://ollama.com/install.sh | sh >> "$LOG_FILE" 2>&1

    # Add Ollama to PATH
    export PATH="$PATH:$HOME/.ollama/bin"
    echo 'export PATH="$PATH:$HOME/.ollama/bin"' >> ~/.bashrc
}

# Configure model with retry logic
setup_model() {
    echo -e "${YELLOW}Setting up Ollama model...${NC}"
    local retries=3
    local delay=10

    for ((i=1; i<=retries; i++)); do
        if ollama pull "$MODEL_NAME" >> "$LOG_FILE" 2>&1; then
            echo -e "${GREEN}Model $MODEL_NAME installed successfully!${NC}"
            return 0
        else
            echo -e "${YELLOW}Model pull failed (attempt $i/$retries). Retrying in $delay seconds...${NC}"
            sleep $delay
        fi
    done

    echo -e "${RED}Failed to install model after $retries attempts.${NC}"
    exit 1
}

# Configure ports for Codespaces visibility
configure_ports() {
    if [ "$CODESPACES" = "true" ]; then
        echo -e "${YELLOW}Configuring forwarded ports...${NC}"
        echo "OLLAMA_PORT=$OLLAMA_PORT" >> "$GITHUB_ENV"
        gh codespace ports visibility "$OLLAMA_PORT":public -c "$CODESPACE_NAME" >> "$LOG_FILE" 2>&1
    fi
}

# Main execution flow
main() {
    echo -e "${GREEN}Starting Codespaces setup...${NC}"
    
    install_packages
    install_python_dependencies
    install_ollama
    setup_model
    configure_ports

    echo -e "${GREEN}\nSetup completed successfully!${NC}"
    echo -e "Run the following commands to get started:"
    echo -e "1. ${YELLOW}ollama serve${NC} - Start Ollama server"
    echo -e "2. Configure your application to use port ${OLLAMA_PORT}"
}

main