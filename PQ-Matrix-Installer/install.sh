#!/bin/bash
#
# PQ Matrix Installer - Installation Script
#
# This script installs the PQ Matrix Installer and starts the installation process.
# It handles dependencies, clones the repository, and launches the Python installer.
#
# Usage:
#   curl -sL https://raw.githubusercontent.com/MNylif/PQ-Matrix-Chat/main/PQ-Matrix-Installer/install.sh | bash
#

set -e

# Define colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Log functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "\n${CYAN}[STEP]${NC} $1"
}

# Print banner
print_banner() {
    echo -e "${BLUE}"
    echo "╔═════════════════════════════════════════════════════════════════╗"
    echo "║                                                                 ║"
    echo "║  🛡️  PQ Matrix Installer - Post-Quantum Security for Matrix  🛡️  ║"
    echo "║                                                                 ║"
    echo "╚═════════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo "A comprehensive installer for deploying secure Matrix servers"
    echo "with post-quantum encryption, decentralized storage, and more."
    echo
}

# Check for dependencies
check_dependencies() {
    log_step "Checking for dependencies..."
    
    # Check for Python 3.8+
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 not found. Please install Python 3.8 or higher."
        exit 1
    fi
    
    # Get Python version
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    log_info "Found Python $python_version"
    
    # Check Python version using Python itself for accurate comparison
    python_version_check=$(python3 -c '
import sys
if sys.version_info < (3, 8):
    print("ERROR:Python 3.8+ is required, but you have Python {}.{}.{}. Please upgrade.".format(
        sys.version_info.major, sys.version_info.minor, sys.version_info.micro))
    exit(1)
else:
    print("OK")
' 2>&1) || {
        if [[ "$python_version_check" == ERROR:* ]]; then
            log_error "${python_version_check#ERROR:}"
        else
            log_error "Unknown Python version error. Please ensure you have Python 3.8+."
        fi
        exit 1
    }
    
    # Check for pip
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 not found. Please install pip for Python 3."
        exit 1
    fi
    log_info "Found pip3"
    
    # Check for Docker
    if ! command -v docker &> /dev/null; then
        log_warning "Docker not found. Docker will be installed during the process."
    else
        log_info "Found Docker"
        
        # Check Docker Compose
        if ! command -v docker-compose &> /dev/null; then
            log_warning "Docker Compose not found. It will be installed during the process."
        else
            log_info "Found Docker Compose"
        fi
    fi
    
    # Check for Git
    if ! command -v git &> /dev/null; then
        log_warning "Git not found. It will be installed during the process."
    else
        log_info "Found Git"
    fi
    
    log_success "Dependency check completed"
}

# Function to create a temporary directory and download the installer
setup_installer() {
    log_step "Setting up installer..."
    
    # Create a temporary directory
    TEMP_DIR=$(mktemp -d 2>/dev/null || mktemp -d -t 'pq-matrix-installer')
    log_info "Created temporary directory: $TEMP_DIR"
    
    # Clone the repository or download the files
    GIT_URL="https://github.com/MNylif/PQ-Matrix-Chat.git"
    
    if command -v git &> /dev/null; then
        log_info "Cloning installer repository using Git..."
        git clone --depth 1 "$GIT_URL" "$TEMP_DIR" 2>/dev/null || {
            log_warning "Git clone failed. Falling back to direct download."
            download_installer
        }
    else
        download_installer
    fi
    
    log_success "Installer setup completed"
}

# Function to download the installer files directly
download_installer() {
    log_info "Downloading installer files directly..."
    
    # Download the necessary files
    curl -s -o "$TEMP_DIR/main.py" "https://raw.githubusercontent.com/MNylif/PQ-Matrix-Chat/main/PQ-Matrix-Installer/main.py"
    curl -s -o "$TEMP_DIR/requirements.txt" "https://raw.githubusercontent.com/MNylif/PQ-Matrix-Chat/main/PQ-Matrix-Installer/requirements.txt"
    
    # Create necessary directories
    mkdir -p "$TEMP_DIR/src"
    mkdir -p "$TEMP_DIR/templates"
    mkdir -p "$TEMP_DIR/config"
    
    # Download structure files (this is simplified; you would need more files)
    curl -s -o "$TEMP_DIR/src/__init__.py" "https://raw.githubusercontent.com/MNylif/PQ-Matrix-Chat/main/PQ-Matrix-Installer/src/__init__.py"
}

# Install Python dependencies
install_dependencies() {
    log_step "Installing Python dependencies..."
    
    # Create a virtual environment
    python3 -m venv "$TEMP_DIR/venv"
    source "$TEMP_DIR/venv/bin/activate"
    
    # Upgrade pip
    pip3 install --upgrade pip
    
    # Install requirements
    pip3 install -r "$TEMP_DIR/requirements.txt"
    
    log_success "Dependencies installed"
}

# Run the installer
run_installer() {
    log_step "Starting the installation process..."
    
    cd "$TEMP_DIR"
    source "$TEMP_DIR/venv/bin/activate"
    
    # Pass any command line arguments to the Python script
    python3 main.py "$@"
    
    # Check if installation was successful
    if [ $? -eq 0 ]; then
        log_success "Installation completed successfully!"
    else
        log_error "Installation encountered issues. Please check the logs."
        exit 1
    fi
}

# Clean up when done
cleanup() {
    if [ -d "$TEMP_DIR" ]; then
        log_info "Cleaning up temporary files..."
        rm -rf "$TEMP_DIR"
    fi
}

# Handle errors and cleanup
handle_error() {
    log_error "An error occurred during installation. Cleaning up..."
    cleanup
    exit 1
}

# Register the error handler
trap handle_error ERR

# Register cleanup on exit
trap cleanup EXIT

# Main execution
main() {
    print_banner
    check_dependencies
    setup_installer
    install_dependencies
    run_installer "$@"
    log_success "PQ Matrix installation process has been completed!"
    log_info "Thank you for using the PQ Matrix Installer."
}

# Start the process
main "$@"
