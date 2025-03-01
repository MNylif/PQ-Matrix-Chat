# 🛡️ PQ Matrix Installer: Post-Quantum Secure Communication

## ⚡ One-Command Installation

```bash
curl -sSL https://raw.githubusercontent.com/MNylif/PQ-Matrix-Installer/main/install.sh | bash
```

## 🌍 Project Summary

In a world where quantum computing and advanced AI threaten traditional encryption methods, communities and organizations need truly secure communication channels. The PQ Matrix Installer provides a fully automated, quantum-resistant deployment system for Matrix servers, ensuring private communications remain private - even against state-sponsored attackers with quantum capabilities.

This project exists to democratize access to post-quantum security, allowing communities to communicate without fear of metadata collection, quantum decryption, or AI-powered surveillance. By combining hardware security modules, distributed trust protocols, and NIST-standardized post-quantum cryptography, we've created a system that's resistant to both current and future threats.

## 🔒 Security Architecture

### Military-Grade Quantum-Resistant Security

- **Post-Quantum Cryptography**: NIST-standardized Kyber-1024 for key encapsulation
- **Hardware Security Module Integration**: FIPS 140-3 Level 3 compliant YubiHSM
- **Distributed Trust Protocol**: 3-of-5 threshold cryptography across geographic regions
- **Zero-Knowledge Audit System**: Memory-mapped Shake-256 hashing with no persistent logs
- **Automated CIS Level 2 Hardening**: Comprehensive server security benchmarks
- **Cloudflare Zero Trust Integration**: Advanced proxy and DDoS protection

## 🚀 Deployment Process

The automated deployment process includes:

1. **Pre-flight System Checks**: Validates all required dependencies
2. **Secure Credential Management**: Encrypts all API keys and credentials
3. **Rclone Configuration**: Sets up encrypted cloud storage
4. **Borg Backup Integration**: Configures quantum-resistant backups
5. **Cloudflare Domain Automation**: Automates DNS and proxy configuration
6. **Server Hardening**: Applies CIS Level 2 security benchmarks
7. **HSM Key Management**: Stores encryption keys in hardware
8. **Distributed Trust Setup**: Splits master keys across geographic regions

## 🔧 Advanced Configuration

### Hardware Security Module Setup

```bash
# Initialize YubiHSM with quantum-resistant algorithms
python deploy.py --init-hsm

# Verify HSM configuration
yubihsm-shell --command="info session"
```

### Distributed Trust Configuration

```bash
# Generate threshold shards (3-of-5)
python deploy.py --generate-shards

# Deploy shards to secure locations
python deploy.py --deploy-shards
```

## 📊 Security Verification

```bash
# Run comprehensive security audit
python deploy.py --audit-security

# Test quantum resistance
python deploy.py --test-quantum-resistance
```

## 🔍 Troubleshooting

### Common Issues

1. **HSM Connection Failure**
   - Ensure YubiHSM is properly connected
   - Verify USB permissions with `lsusb`

2. **Shard Deployment Failure**
   - Check SSH keys for remote servers
   - Verify network connectivity to shard locations

3. **Quantum Library Issues**
   - Install liboqs dependencies: `apt install liboqs-dev`
   - Update to latest version: `pip install -U liboqs`

## 🤝 Contributing

We welcome contributions to enhance the security and usability of this project:

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔐 Security Features

- ✅ Kyber-1024 Post-Quantum Encryption
- ✅ Hardware Security Module Integration
- ✅ Distributed Trust Protocol (3-of-5)
- ✅ Zero-Knowledge Audit System
- ✅ Geographic Shard Distribution
- ✅ Memory-Safe Implementation
- ✅ CIS Level 2 Server Hardening
- ✅ Cloudflare Zero Trust Integration
- ✅ Atomic Operations with Rollback
- ✅ Immutable Audit Logging
