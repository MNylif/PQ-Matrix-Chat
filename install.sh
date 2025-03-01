#!/bin/bash

# Automated deployment installer
set -e

# Install system dependencies
sudo apt-get update
sudo apt-get install -y \
    python3 \
    python3-venv \
    python3-pip \
    rclone \
    borgbackup \
    libxxhash-dev

# Create project directory
PROJECT_DIR="${HOME}/pq-matrix-deploy"
mkdir -p "${PROJECT_DIR}"
cd "${PROJECT_DIR}"

# Set up Python environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python requirements
curl -sSL https://raw.githubusercontent.com/yourusername/pq-matrix/main/requirements.txt -o requirements.txt
python3 -m pip install -r requirements.txt

# Download deployment script
curl -sSL https://raw.githubusercontent.com/yourusername/pq-matrix/main/deploy.py -o deploy.py
chmod +x deploy.py

# Start configuration
./deploy.py
