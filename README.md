# Deploying Deepseek AI in GitHub Codespaces

This guide outlines the steps to set up and run Deepseek AI in GitHub Codespaces efficiently.

## Prerequisites

Ensure the following before setup:
- A GitHub Codespace with adequate resources
- Basic CLI and shell scripting knowledge
- Installed dependencies:
  - [Ollama](https://ollama.ai) for AI execution
  - [Glances](https://nicolargo.github.io/glances/) for monitoring
- Machine specs: 4-core CPU, 16GB RAM, 32GB storage (or higher recommended)

## Installation & Execution

### 1. Setup
Clone the repository and configure the environment:
```bash
git clone https://github.com/Paopun20/Deepseek-In-Codespace.git
cd Deepseek-In-Codespace
chmod +x *.sh
./setup.sh
```

### 2. Launching Services
Start each service in a separate terminal session:
- **Terminal 1:** Start the Ollama AI model service
  ```bash
  ./runOllama.sh
  ```
- **Terminal 2:** Run the Deepseek application
  ```bash
  ./Deepseek.sh
  ```
- **Terminal 3:** Monitor system performance
  ```bash
  ./runGlances.sh
  ```

## Optimization Tips
- Increase CPU/RAM in Codespace settings for better performance.
- Use Glances to monitor resource usage.
- Automate repetitive setup tasks.
- Keep software updated for improvements.
- Manage resources effectively when running multiple models.

By following these steps, you can efficiently deploy Deepseek AI in GitHub Codespaces for a seamless AI-driven workflow.

