# Kanuka

## Setup on AWS

### Install Git
```bash
sudo yum install git -y
```

### Verify installation
```bash
git --version
```

### Clone the repository
```bash
git clone https://github.com/Pingeat/TFC--Internal-bot.git
```

### Install Python 3 and pip
```bash
sudo yum install python3 python3-pip -y
python3 --version
pip3 --version
```

### Install dependencies
```bash
pip3 install -r requirements.txt
```

### Install Redis
```bash
sudo dnf install redis6
```

## Node.js Rewrite (Work in Progress)
A minimal Node.js server has been added and will gradually replace the Python backend.

### Run
```bash
node server.js
```
