# sh code
# setup.sh
sudo apt update -y
sudo apt-get update -y
sudo apt-get update -y --fix-missing
sudo yum install -y python3 python3-pip
python3 -m pip install --upgrade pip
sudo apt install -y glances
curl -fsSL https://ollama.com/install.sh | sh
pip3 install flask ngrok python-dotenv