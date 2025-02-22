# sh code
# setup.sh
sudo apt update -y
sudo apt install -y glances
curl -fsSL https://ollama.com/install.sh | sh
sudo yum install -y python3 python3-pip
python3 -m pip install --upgrade pip
pip3 install flask ngrok