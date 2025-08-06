"# kanuka" 


#To install a bot in aws
# Install Git
sudo yum install git -y

# Verify installation
git --version

# Now you can clone the repository
git clone https://github.com/Pingeat/TFC--Internal-bot.git


# First, install Python 3 and pip
sudo yum install python3 python3-pip -y

# Verify the installation
python3 --version
pip3 --version

# Now install your requirements using pip3
pip3 install -r requirements.txt

# Install Redis
sudo dnf install redis6