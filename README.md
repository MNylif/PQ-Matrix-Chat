# 🛡️ PQ Matrix Installer

An automated installer for deploying a secure, quantum-resistant Matrix chat server with a single command.

## 🚀 Quick Start

Just run the following command and follow the prompts:

```bash
curl -sL https://raw.githubusercontent.com/your-org/pq-matrix-installer/main/install.sh | bash
```

## 🔐 What Is PQ Matrix?

PQ Matrix is a secure, privacy-focused Matrix server setup that features:

- ✅ **Post-quantum encrypted** TURN server (Kyber-1024)
- ✅ End-to-end encrypted voice/video calls
- ✅ Single Sign-On (SSO) via Keycloak
- ✅ GitLab webhook integration
- ✅ Storj decentralized storage
- ✅ Cloudflare DNS & proxy integration
- ✅ Adaptive resource optimization
- ✅ Zero-logs policy with metadata scrubbing

## 🛠️ Features of the Installer

### 📋 Automated Installation Phases

The installer breaks down the setup process into clear phases:

1. **Pre-Flight Checks**: System requirements verification
2. **Configuration**: Interactive setup with user input
3. **Domain Setup**: Cloudflare DNS automation
4. **Service Installation**: Docker, Docker Compose, dependencies
5. **Matrix Server Setup**: Conduit, COTURN, Nginx configuration
6. **Security Configuration**: TLS, post-quantum encryption
7. **Storage Integration**: Rclone and Storj setup
8. **Backup Configuration**: Automated backup with retention policy
9. **Hardening**: Server security enforcement
10. **Finalization**: Post-install verification

### ⚙️ Adaptive Resource Optimization

The installer includes intelligent resource optimization:

- **Hardware Detection**: Automatically detects CPU cores, memory, and disk space
- **Optimization Levels**: 
  - `Low`: Kyber-512, minimal resources (70% memory utilization)
  - `Standard`: Kyber-768, balanced (80% memory utilization)
  - `High`: Kyber-1024, maximum security (90% memory utilization)
- **Auto-Downgrade**: When hardware constraints are detected

### 🔒 Security Practices

- **Pre-Flight Checks**: System validation before installation
- **Atomic Operations**: With rollback capabilities if steps fail
- **Audit Logging**: Detailed installation logs
- **Encrypted Storage**: For all sensitive credentials
- **No-Logs Policy**: Implementation of data minimization

## 📝 Configuration Options

The installer supports both interactive and non-interactive modes:

### Interactive Mode (Default)

Run without arguments for a step-by-step guided setup:

```bash
curl -sL https://raw.githubusercontent.com/your-org/pq-matrix-installer/main/install.sh | bash
```

### Advanced Options

```
--optimization-level [low|standard|high]  Set resource optimization level
--debug                                   Enable verbose logging
--non-interactive                         Run with predefined config
--config FILE                             Path to config file
--skip-phases PHASES                      Comma-separated phases to skip
--only-phase PHASE                        Run only a specific phase
```

## 📊 System Requirements

- **CPU**: 2+ cores (4+ recommended for high optimization)
- **RAM**: 2GB+ (4GB+ recommended)
- **Storage**: 20GB+ free space
- **OS**: Ubuntu 20.04+, Debian 11+, or similar Linux
- **Network**: Ports 80, 443, 3478, 5349 available

## 🌐 Cloudflare Integration

The installer automates Cloudflare DNS setup and proxy configuration:

- Automatic DNS record creation
- Cloudflare proxy integration for additional security
- Certificate management

## ⚠️ Security Best Practices

- Regularly update with `pq-matrix update`
- Rotate encryption keys quarterly (automated by default)
- Monitor logs for suspicious activity
- Follow the 3-2-1 backup rule (3 copies, 2 storage types, 1 offsite)

## 📜 License

No commercial rights or licenses are granted. This project is in the public domain.

## 📚 Documentation

Detailed documentation can be found in the [docs](./docs) directory.

The original Matrix server deployment instructions have been archived to [docs/archived/README-original.md](./docs/archived/README-original.md).
