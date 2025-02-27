#!/bin/bash

# =============================================
#           CODESPACES SETUP SCRIPT
# =============================================

set -euo pipefail

# --------------------------
#      CONFIGURATION
# --------------------------
MODEL_NAME="deepseek-r1:7b"
OLLAMA_PORT=11434
LOG_FILE="codespaces_setup.log"
CODESPACES="${CODESPACES:-false}"

# Color Palette
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Formatting
BOLD='\033[1m'
DIM='\033[2m'
UNDERLINE='\033[4m'

# --------------------------
#      INITIALIZATION
# --------------------------
echo -e "${MAGENTA}\n🚀 Starting Codespaces setup - $(date)${NC}\n" | tee -a "$LOG_FILE"
trap 'echo -e "${RED}\n⛔ Setup interrupted! Exiting...${NC}"; exit 1' INT

# =============================================
#               FUNCTIONS
# =============================================

# --------------------------
#     ERROR HANDLING
# --------------------------
handle_error() {
    local line="$1"
    local message="$2"
    echo -e "${RED}█▓▒░ ERROR on line ${line}: ${message}${NC}" | tee -a "$LOG_FILE"
    exit 1
}
trap 'handle_error $LINENO "$BASH_COMMAND"' ERR

# --------------------------
#     FORMATTED OUTPUT
# --------------------------
log_header() {
    echo -e "${CYAN}\n▄▀▀▄▀▀▄▀▀▄▀▀▄▀▀▄▀▀▄▀▀▄▀▀▄▀▀▄▀▀▄▀▀▄▀▀▄▀▀▄"
    echo -e "█ ${1}"
    echo -e "▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀▄▀${NC}"
}

log_success() {
    echo -e "${GREEN}✅ ${1}${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}⚠️  ${1}${NC}" | tee -a "$LOG_FILE"
}

log_progress() {
    echo -e "${DIM}⌛ ${1}...${NC}" | tee -a "$LOG_FILE"
}

# --------------------------
#     SYSTEM COMMANDS
# --------------------------
run_command() {
    echo -e "${DIM}\$ ${1}${NC}" | tee -a "$LOG_FILE"
    eval "$1" >> "$LOG_FILE" 2>&1
}

# =============================================
#               MAIN OPERATIONS
# =============================================

install_packages() {
    log_header "SYSTEM PACKAGE INSTALLATION"
    run_command "sudo apt-get update -y"
    run_command "sudo apt install -y pciutils python3 python3-pip curl"
    log_success "System dependencies installed"
}

install_python_dependencies() {
    log_header "PYTHON ENVIRONMENT SETUP"
    run_command "pip install -r requirements.txt"
    log_success "Python dependencies installed"
}

install_ollama() {
    log_header "OLLAMA INSTALLATION"
    run_command "curl -fsSL https://ollama.com/install.sh | sh"
    export PATH="$PATH:$HOME/.ollama/bin"
    echo 'export PATH="$PATH:$HOME/.ollama/bin"' >> ~/.bashrc
    log_success "Ollama installed successfully"
}

setup_model() {
    log_header "MODEL CONFIGURATION"
    
    if ollama list | grep -q "$MODEL_NAME"; then
        log_success "Model ${MODEL_NAME} already exists"
        return 0
    fi

    log_progress "Starting Ollama service"
    ollama serve > /dev/null 2>&1 &
    local ollama_pid=$!

    wait_for_ollama

    log_progress "Downloading AI model (${MODEL_NAME})"
    local retries=3
    local delay=10
    
    for ((i=1; i<=retries; i++)); do
        if ollama pull "$MODEL_NAME"; then
            log_success "Model downloaded successfully"
            kill $ollama_pid
            wait $ollama_pid 2>/dev/null
            return 0
        else
            log_warning "Download attempt ${i}/${retries} failed"
            sleep $delay
        fi
    done
    
    handle_error $LINENO "Failed to download model after ${retries} attempts"
}

wait_for_ollama() {
    log_progress "Waiting for Ollama to start"
    local timeout=30
    
    while ! curl -s "http://localhost:${OLLAMA_PORT}" > /dev/null; do
        sleep 1
        ((timeout--))
        
        if [ $timeout -eq 0 ]; then
            handle_error $LINENO "Ollama failed to start within 30 seconds"
        fi
    done
}

configure_ports() {
    if [ "$CODESPACES" = "true" ]; then
        log_header "CODESPACES CONFIGURATION"
        # Use default environment file path if not set
        local env_file="${GITHUB_ENV:-$HOME/.env}"
        run_command "echo 'OLLAMA_PORT=${OLLAMA_PORT}' >> \"${env_file}\""
        
        if [ -n "${CODESPACE_NAME:-}" ]; then
            run_command "gh codespace ports visibility ${OLLAMA_PORT}:public -c \"${CODESPACE_NAME}\""
            log_success "Port ${OLLAMA_PORT} configured for public access"
        else
            log_warning "CODESPACE_NAME not found - port visibility not configured"
        fi
    fi
}

show_completion() {
    echo -e "${GREEN}"
    echo "============================================="
    echo "           SETUP COMPLETE! 🎉               "
    echo "============================================="
    echo -e "${NC}"
    echo -e "${BOLD}Next steps:${NC}"
    echo -e "1. ${YELLOW}ollama serve${NC}    - Start the Ollama server"
    echo -e "2. Configure your application to use port ${UNDERLINE}${OLLAMA_PORT}${NC}"
    echo -e "\n${DIM}Need help? Check the log file: ${LOG_FILE}${NC}"
}

# =============================================
#               MAIN EXECUTION
# =============================================
main() {
    install_packages
    install_python_dependencies
    install_ollama
    setup_model
    configure_ports
    show_completion
}

main