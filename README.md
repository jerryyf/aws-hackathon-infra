# aws-hackathon-infra

Repository for AWS Hackathon AgentCore infrastructure.

> Note on AI-generated content: AI coding agents are used here to accelerate development. However **organic** content (i.e. code/documentation a human wrote) should be clearly tagged - for example in the commit message. Organic content can include AI-enhanced content where sensibly reviewed. Perhaps an opinionated perspective, but it is easier for humans to review organic code than it is to review AI-generated code.

## Prerequisites
- opencode
- access to a model with strong coding capabilities and tool use (e.g. Claude Sonnet 4, OpenAI Codex)
- spec-kit
- aws-cdk

## Setup

### Prerequisites
- **Python 3.11+**
- **Node.js 18+** (for AWS CDK CLI)
- **AWS CLI** configured with appropriate credentials
- **Git**

### macOS Setup

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
cd aws-hackathon-infra

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

### Linux Setup

#### Ubuntu/Debian

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
cd aws-hackathon-infra

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

#### Fedora/RHEL/CentOS

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
cd aws-hackathon-infra

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

### Windows Setup (WSL2 - Ubuntu)

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
cd aws-hackathon-infra

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

### Running Tests

```bash
# From repository root
PYTHONPATH=. pytest

# Run specific test
PYTHONPATH=. pytest tests/unit/test_vpc_construct.py::test_vpc_construct

# Run contract tests
PYTHONPATH=. pytest tests/contract/ -v

# Run with coverage
PYTHONPATH=. pytest --cov=cdk --cov-report=html
```

### Deploying Infrastructure

See [quickstart.md](specs/002-create-python-application/quickstart.md) for detailed deployment scenarios and validation procedures.

## Guidelines
AGENTS.md should be updated with `/init` frequently. The platform that the agent was run on must be included. Only perform manual edits to documentation.
