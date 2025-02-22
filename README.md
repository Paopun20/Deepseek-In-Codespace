<div align="center">
  <img src="https://github.com/deepseek-ai/DeepSeek-V2/blob/main/figures/logo.svg?raw=true" width="60%" alt="DeepSeek-R1" />
</div>
<hr>

# Deepseek In GitHub Codespace

This project enables you to run Deepseek AI within a GitHub Codespace. Follow the instructions below to set up and launch the service.

## Prerequisites

- A GitHub Codespace environment
- Familiarity with basic terminal commands
- [Ollama](https://ollama.ai) installed
- [Glances](https://nicolargo.github.io/glances/) installed for monitoring
- New Codespaces
- Change codespace machine type to 4-core 16GB RAM 32GB

## Setup & Execution

### 1. Initial Setup

Clone the repository, navigate into the project directory, and prepare the scripts for execution:

```bash
git clone https://github.com/your-username/Deepseek-In-Codespace.git
cd Deepseek-In-Codespace
chmod +x *.sh
./setup.sh
```

### 2. Running the Services

Launch each service in a separate terminal session:

- **Terminal 1: Start the Ollama Service**
  ```bash
  ./runOllama.sh
  ```
  
- **Terminal 2: Launch the Deepseek Application**
  ```bash
  ./Deepseek.sh
  ```

- **Terminal 3: Begin Monitoring with Glances**
  ```bash
  ./runGlances.sh
  ```