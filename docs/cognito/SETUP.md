# Setup

## Prerequisites
- **Python 3.11+**
- **Node.js 18+** (for AWS CDK CLI)
- **AWS CLI** configured with appropriate credentials
- **Git**

## macOS Setup

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11+
brew install python@3.11

# Install Node.js 18+
brew install node@18

# Install AWS CLI
brew install awscli

# Configure AWS credentials
aws configure

# Clone repository
git clone <repo-url>
cd aws-bidopsai-infra

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
cd cdk
pip install -r requirements.txt

# Install AWS CDK CLI globally
npm install -g aws-cdk

# Bootstrap CDK (first time only, per region/account)
cdk bootstrap aws://ACCOUNT-ID/REGION

# Verify installation
cdk --version
pytest --version
```

## Linux Setup

### Ubuntu/Debian

```bash
# Update package manager
sudo apt update

# Install Python 3.11+
sudo apt install python3.11 python3.11-venv python3-pip

# Install Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS credentials
aws configure

# Clone repository
git clone <repo-url>
cd aws-bidopsai-infra

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
cd cdk
pip install -r requirements.txt

# Install AWS CDK CLI globally
sudo npm install -g aws-cdk

# Bootstrap CDK (first time only, per region/account)
cdk bootstrap aws://ACCOUNT-ID/REGION

# Verify installation
cdk --version
pytest --version
```

### Fedora/RHEL/CentOS

```bash
# Update package manager
sudo dnf update -y

# Install Python 3.11+
sudo dnf install python3.11 python3-pip

# Install Node.js 18+
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo dnf install -y nodejs

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS credentials
aws configure

# Clone repository
git clone <repo-url>
cd aws-bidopsai-infra

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
cd cdk
pip install -r requirements.txt

# Install AWS CDK CLI globally
sudo npm install -g aws-cdk

# Bootstrap CDK (first time only, per region/account)
cdk bootstrap aws://ACCOUNT-ID/REGION

# Verify installation
cdk --version
pytest --version
```

## Windows Setup (WSL2 - Ubuntu)

```bash
# Install WSL2 (PowerShell as Administrator)
# wsl --install -d Ubuntu-22.04

# Once inside WSL2 Ubuntu terminal:

# Update package manager
sudo apt update && sudo apt upgrade -y

# Install Python 3.11+
sudo apt install python3.11 python3.11-venv python3-pip

# Install Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS credentials
aws configure

# Clone repository
git clone <repo-url>
cd aws-bidopsai-infra

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
cd cdk
pip install -r requirements.txt

# Install AWS CDK CLI globally
sudo npm install -g aws-cdk

# Bootstrap CDK (first time only, per region/account)
cdk bootstrap aws://ACCOUNT-ID/REGION

# Verify installation
cdk --version
pytest --version
```