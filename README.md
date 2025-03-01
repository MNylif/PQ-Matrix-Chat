# 🛡️ Quantum-Resistant Matrix Server Deployment

A complete guide to deploying a secure Conduit Matrix server with post-quantum encryption, decentralized storage, and third-party integrations.

## 📋 Features

- ✅ Post-quantum encrypted TURN server (Kyber-1024)
- ✅ End-to-end encrypted voice/video calls
- ✅ Single Sign-On (SSO) via Keycloak
- ✅ GitLab webhook integration
- ✅ Storj decentralized storage
- ✅ OpenProject widgets integration
- ✅ Database encryption with quantum-resistant algorithms

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Domain name with DNS configured
- Valid SSL certificates

### Directory Structure Setup

```bash
# Create project structure
mkdir -p ~/matrix-server/{conduit,coturn,nginx,keycloak,hookshot,scripts,certs}

# Move to project directory
cd ~/matrix-server
```

## 🔧 Installation & Configuration

### 1️⃣ Conduit Matrix Server Setup

Create Docker Compose file:

```bash
cat > docker-compose.yml << 'EOF'
version: '3'

services:
  # Matrix Conduit Server
  conduit:
    image: matrixconduit/matrix-conduit:latest
    container_name: conduit
    restart: unless-stopped
    volumes:
      - ./conduit/data:/var/lib/matrix-conduit
      - ./conduit/config:/etc/matrix-conduit
    environment:
      - CONDUIT_SERVER_NAME=yourdomain.com
      - CONDUIT_DATABASE_BACKEND=rocksdb
      - CONDUIT_ALLOW_REGISTRATION=false
      - CONDUIT_ALLOW_FEDERATION=true
      - CONDUIT_MAX_REQUEST_SIZE=20_000_000
      - CONDUIT_TURN_URIS='["turns:turn.yourdomain.com?transport=udp", "turns:turn.yourdomain.com?transport=tcp"]'
      - CONDUIT_TURN_SECRET=${TURN_SECRET}
    ports:
      - "8455:6167"
    networks:
      - matrix-net

  # Post-Quantum TURN Server
  coturn:
    image: coturn/coturn:latest
    container_name: coturn
    restart: unless-stopped
    volumes:
      - ./coturn/turnserver.conf:/etc/turnserver.conf
      - ./certs:/etc/certs
    network_mode: host
    depends_on:
      - conduit

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: nginx
    restart: unless-stopped
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/certs
    ports:
      - "80:80"
      - "443:443"
    networks:
      - matrix-net
    depends_on:
      - conduit

  # Keycloak SSO Provider
  keycloak:
    image: quay.io/keycloak/keycloak:latest
    container_name: keycloak
    restart: unless-stopped
    environment:
      - KEYCLOAK_ADMIN=admin
      - KEYCLOAK_ADMIN_PASSWORD=${KEYCLOAK_ADMIN_PASSWORD}
      - KC_DB=postgres
      - KC_DB_URL_HOST=postgres
      - KC_DB_URL_DATABASE=keycloak
      - KC_DB_USERNAME=keycloak
      - KC_DB_PASSWORD=${KEYCLOAK_DB_PASSWORD}
    command: start-dev
    volumes:
      - ./keycloak/data:/opt/keycloak/data
    ports:
      - "8080:8080"
    networks:
      - matrix-net
    depends_on:
      - postgres

  # PostgreSQL for Keycloak
  postgres:
    image: postgres:14-alpine
    container_name: postgres
    restart: unless-stopped
    environment:
      - POSTGRES_DB=keycloak
      - POSTGRES_USER=keycloak
      - POSTGRES_PASSWORD=${KEYCLOAK_DB_PASSWORD}
    volumes:
      - ./postgres/data:/var/lib/postgresql/data
    networks:
      - matrix-net

  # GitLab Webhook Integration
  hookshot:
    image: matrixdotorg/hookshot:latest
    container_name: hookshot
    restart: unless-stopped
    volumes:
      - ./hookshot/config.yml:/config/config.yml
    ports:
      - "9000:9000"
    networks:
      - matrix-net
    depends_on:
      - conduit

networks:
  matrix-net:
    driver: bridge
EOF
```

Create environment variables file:

```bash
cat > .env << 'EOF'
# Generate secure secrets with: openssl rand -base64 48
TURN_SECRET=generate_a_secure_secret_here
KEYCLOAK_ADMIN_PASSWORD=change_this_password
KEYCLOAK_DB_PASSWORD=change_this_password_too
EOF

# Generate secure TURN secret
TURN_SECRET=$(openssl rand -base64 48)
sed -i "s/generate_a_secure_secret_here/$TURN_SECRET/" .env
```

### 2️⃣ Post-Quantum TURN Server Configuration

Create the Coturn configuration:

```bash
cat > coturn/turnserver.conf << 'EOF'
# TURN server configuration
use-auth-secret
static-auth-secret=${TURN_SECRET}
realm=yourdomain.com

# TLS configuration
cert=/etc/certs/fullchain.pem
pkey=/etc/certs/privkey.pem
dh-file=/etc/certs/dhparam-kyber1024.pem
cipher-list=KYBER1024-ECDHE-ECDSA-AES256-GCM-SHA384

# Network settings
listening-port=3478
tls-listening-port=5349
no-udp
no-tcp
no-tls
no-dtls
no-cli
secure-stun

# Logging
verbose
fingerprint
EOF

# Generate Kyber-optimized DH parameters
openssl genpkey -algorithm kyber1024 -out certs/dhparam-kyber1024.pem
```

### 3️⃣ Nginx Reverse Proxy Configuration

Create Nginx configuration:

```bash
cat > nginx/nginx.conf << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                     '$status $body_bytes_sent "$http_referer" '
                     '"$http_user_agent" "$http_x_forwarded_for"';
    access_log /var/log/nginx/access.log main;
    sendfile on;
    keepalive_timeout 65;
    server_tokens off;
    include /etc/nginx/conf.d/*.conf;
}
EOF

cat > nginx/conf.d/matrix.conf << 'EOF'
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/certs/fullchain.pem;
    ssl_certificate_key /etc/certs/privkey.pem;
    ssl_dhparam /etc/certs/dhparam-kyber1024.pem;
    
    ssl_protocols TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers KYBER1024-ECDHE-ECDSA-AES256-GCM-SHA384;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-XSS-Protection "1; mode=block";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; connect-src 'self' wss://yourdomain.com; frame-src 'self'; object-src 'none';";

    # Matrix client-server API
    location /_matrix {
        proxy_pass http://conduit:6167;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 600;
        client_max_body_size 20M;
    }

    # Matrix federation API
    location /.well-known/matrix {
        root /var/www/html;
        default_type application/json;
        add_header Access-Control-Allow-Origin *;
    }

    # Element client
    location / {
        root /var/www/html/element;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
}

# Turn server configuration
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name turn.yourdomain.com;

    ssl_certificate /etc/certs/fullchain.pem;
    ssl_certificate_key /etc/certs/privkey.pem;
    ssl_dhparam /etc/certs/dhparam-kyber1024.pem;
    
    ssl_protocols TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers KYBER1024-ECDHE-ECDSA-AES256-GCM-SHA384;
    
    # Redirect all HTTP traffic to local TURN server
    location / {
        return 404;
    }
}
EOF
```

### 4️⃣ Conduit Server Configuration

Create Conduit configuration:

```bash
cat > conduit/config/conduit.toml << 'EOF'
[global]
server_name = "yourdomain.com"
database_backend = "rocksdb"
database_path = "/var/lib/matrix-conduit/db"
allow_registration = false
allow_federation = true

[client]
max_request_size = 20_000_000
address = "0.0.0.0"
port = 6167

[turn]
uris = ["turns:turn.yourdomain.com?transport=udp", "turns:turn.yourdomain.com?transport=tcp"]
secret = "${TURN_SECRET}"

# Post-Quantum Database Encryption
[database]
encryption_key = "k.super_secure_key:kyber1024"

# SSO Configuration
[oidc]
issuer = "https://yourdomain.com/auth/realms/matrix"
client_id = "matrix-conduit"
client_secret = "your_client_secret"

# Media Storage with Storj
[media.storage]
type = "s3"
endpoint = "https://gateway.storjshare.io"
bucket_name = "matrix-media"
access_key = "your_storj_access_key"
secret_key = "your_storj_secret"
region = "us-central-1"

[media.encryption]
algorithm = "kyber1024-rsa-oae"
public_key_file = "/etc/matrix-conduit/pqc_media.pub"
private_key_file = "/etc/matrix-conduit/pqc_media.key"

# Widget Configuration
[widgets]
enable_authenticated_widgets = true
EOF

# Generate post-quantum media encryption keys
mkdir -p conduit/config
openssl genpkey -algorithm kyber1024 -out conduit/config/pqc_media.key
openssl pkey -pubout -in conduit/config/pqc_media.key -out conduit/config/pqc_media.pub
```

### 5️⃣ GitLab Webhook Integration

Create the hookshot configuration:

```bash
cat > hookshot/config.yml << 'EOF'
gitlab:
  instances:
    gitlab.com:
      webhook:
        secret: your_webhook_secret
        publicUrl: https://yourdomain.com/webhooks/
  bindAddress: 0.0.0.0
  port: 9000
  
homeserver:
  url: http://conduit:6167
  domain: yourdomain.com
  
# Login credentials for the Matrix bot
auth:
  type: password
  username: hookshot
  password: your_bot_password
EOF

# Generate webhook secret
WEBHOOK_SECRET=$(openssl rand -base64 32)
sed -i "s/your_webhook_secret/$WEBHOOK_SECRET/" hookshot/config.yml
```

### 6️⃣ Element Client Configuration

Download and configure Element client:

```bash
mkdir -p nginx/html/element
cd nginx/html/element

# Download Element Web client
curl -Lo element.tar.gz https://github.com/vector-im/element-web/releases/latest/download/element-web.tar.gz
tar -xzf element.tar.gz --strip-components=1
rm element.tar.gz

# Create Element configuration
cat > config.json << 'EOF'
{
  "default_server_config": {
    "m.homeserver": {
      "base_url": "https://yourdomain.com",
      "server_name": "yourdomain.com"
    },
    "m.identity_server": {
      "base_url": "https://vector.im"
    }
  },
  "brand": "Your Organization Matrix",
  "integrations_ui_url": "https://scalar.vector.im/",
  "integrations_rest_url": "https://scalar.vector.im/api",
  "integrations_widgets_urls": [
    "https://scalar.vector.im/_matrix/integrations/v1",
    "https://scalar.vector.im/api"
  ],
  "default_theme": "light",
  "features": {
    "feature_thread": true,
    "feature_pinning": true,
    "feature_custom_status": true,
    "feature_custom_tags": true,
    "feature_state_counters": true,
    "feature_many_integration_managers": true,
    "feature_mjolnir": true,
    "feature_html_status": true,
    "feature_element_call_v2": true
  },
  "widget_build_url": "https://call.yourdomain.com/config.json",
  "posthog": {
    "projectApiKey": "",
    "apiHost": ""
  },
  "setting_defaults": {
    "breadcrumbs": true,
    "MessageComposerInput.autoReplaceEmoji": true,
    "MessageComposerInput.showStickersButton": true,
    "MessageComposerInput.insertTrailingColon": true,
    "useCompactLayout": false
  },
  "disable_custom_urls": false,
  "disable_guests": true,
  "disable_login_language_selector": false,
  "disable_3pid_login": false
}
EOF

cd ~/matrix-server
```

### 7️⃣ Keycloak SSO Setup

```bash
# Start Keycloak first to set it up
docker-compose up -d keycloak postgres

# Wait for Keycloak to start (30 seconds)
echo "Waiting for Keycloak to start..."
sleep 30

# Create setup script
cat > scripts/setup-keycloak.sh << 'EOF'
#!/bin/bash

# Variables
KEYCLOAK_URL="http://localhost:8080"
KEYCLOAK_ADMIN="admin"
KEYCLOAK_ADMIN_PASSWORD="$KEYCLOAK_ADMIN_PASSWORD"
REALM_NAME="matrix"
CLIENT_ID="matrix-conduit"
CLIENT_SECRET="$(openssl rand -base64 32)"

# Get admin token
ADMIN_TOKEN=$(curl -s -X POST "${KEYCLOAK_URL}/realms/master/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${KEYCLOAK_ADMIN}" \
  -d "password=${KEYCLOAK_ADMIN_PASSWORD}" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" | jq -r '.access_token')

# Create Matrix realm
curl -s -X POST "${KEYCLOAK_URL}/admin/realms" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "realm": "'"${REALM_NAME}"'",
    "enabled": true,
    "displayName": "Matrix",
    "registrationAllowed": false
  }'

# Create Matrix client
CLIENT_RESPONSE=$(curl -s -X POST "${KEYCLOAK_URL}/admin/realms/${REALM_NAME}/clients" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "'"${CLIENT_ID}"'",
    "secret": "'"${CLIENT_SECRET}"'",
    "enabled": true,
    "protocol": "openid-connect",
    "publicClient": false,
    "redirectUris": [
      "https://yourdomain.com/_matrix/client/r0/login/sso/redirect"
    ],
    "webOrigins": [
      "https://yourdomain.com"
    ],
    "standardFlowEnabled": true,
    "implicitFlowEnabled": false,
    "directAccessGrantsEnabled": true,
    "serviceAccountsEnabled": true,
    "authorizationServicesEnabled": true
  }')

# Update Conduit config with client secret
sed -i "s/your_client_secret/${CLIENT_SECRET}/" ../conduit/config/conduit.toml

echo "Keycloak setup complete!"
echo "Client Secret: ${CLIENT_SECRET}"
EOF

chmod +x scripts/setup-keycloak.sh
./scripts/setup-keycloak.sh
```

### 8️⃣ Storj Integration Setup

```bash
# Create script to set up Storj
cat > scripts/setup-storj.sh << 'EOF'
#!/bin/bash

# Install Storj CLI
curl -L https://github.com/storj/storj/releases/latest/download/uplink_linux_amd64.zip -o uplink.zip
unzip uplink.zip
chmod +x uplink
sudo mv uplink /usr/local/bin/

# Log in to Storj
echo "Please create a Storj account at https://storj.io and generate an access grant"
echo -n "Enter your Storj access grant: "
read ACCESS_GRANT
uplink import --force "matrix-access" "$ACCESS_GRANT"

# Create bucket for Matrix media
uplink mb sj://matrix-media

# Get access and secret keys
ACCESS_KEY=$(uplink share --readonly=false --disallow-writes=false --disallow-deletes=false sj://matrix-media | grep "Access Key" | awk '{print $3}')
SECRET_KEY=$(uplink share --readonly=false --disallow-writes=false --disallow-deletes=false sj://matrix-media | grep "Secret Key" | awk '{print $3}')

# Update Conduit config
sed -i "s/your_storj_access_key/$ACCESS_KEY/" ../conduit/config/conduit.toml
sed -i "s/your_storj_secret/$SECRET_KEY/" ../conduit/config/conduit.toml

echo "Storj setup complete!"
EOF

chmod +x scripts/setup-storj.sh
```

### 9️⃣ Deploy Everything

```bash
# Start the services
docker-compose up -d

# Check status
docker-compose ps
```

### 🔟 Configure DNS Records

Create the following DNS records:

```
Type  | Name               | Value
------|--------------------|-----------------
A     | yourdomain.com     | Your server IP
A     | turn.yourdomain.com| Your server IP
SRV   | _matrix._tcp       | 10 0 443 yourdomain.com
```

Create .well-known files for Matrix server discovery:

```bash
mkdir -p nginx/html/.well-known/matrix
cat > nginx/html/.well-known/matrix/server << 'EOF'
{
  "m.server": "yourdomain.com:443"
}
EOF

cat > nginx/html/.well-known/matrix/client << 'EOF'
{
  "m.homeserver": {
    "base_url": "https://yourdomain.com"
  },
  "m.identity_server": {
    "base_url": "https://vector.im"
  }
}
EOF
```

## 🛠️ Maintenance

### Certbot SSL Certificate Setup

First, install Certbot:

```bash
# Install Certbot and Nginx plugin
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# Create script for initial certificate generation
cat > scripts/setup-certs.sh << 'EOF'
#!/bin/bash

# Variables
DOMAIN="yourdomain.com"
EMAIL="admin@yourdomain.com"
DOMAINS="-d $DOMAIN -d turn.$DOMAIN"

# Stop Nginx if running to free up port 80
docker-compose stop nginx || true

# Generate certificates
sudo certbot certonly --standalone \
  --agree-tos --non-interactive \
  --preferred-challenges http \
  --email $EMAIL \
  $DOMAINS \
  --rsa-key-size 4096 \
  --preferred-chain "ISRG Root X1 (Kyber Hybrid)" \
  --cert-name $DOMAIN

# Create certs directory
mkdir -p ~/matrix-server/certs

# Copy certificates
sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ~/matrix-server/certs/
sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ~/matrix-server/certs/
sudo chmod 644 ~/matrix-server/certs/*.pem

# Set proper ownership
sudo chown $USER:$USER ~/matrix-server/certs/*.pem

echo "SSL certificates generated at $(date)"
EOF

chmod +x scripts/setup-certs.sh
./scripts/setup-certs.sh
```

### Automated SSL Renewal

Set up more frequent renewal checks (Certbot will only renew when necessary):

```bash
cat > scripts/renew-certs.sh << 'EOF'
#!/bin/bash

# Variables
DOMAIN="yourdomain.com"
LOG_FILE=~/matrix-server/logs/cert-renewal.log
mkdir -p ~/matrix-server/logs

# Stop Nginx temporarily if needed
docker-compose stop nginx

# Renew certificates with post-quantum preference
sudo certbot renew --quiet --preferred-chain "ISRG Root X1 (Kyber Hybrid)" \
  --post-hook "cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ~/matrix-server/certs/ && \
               cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ~/matrix-server/certs/ && \
               chmod 644 ~/matrix-server/certs/*.pem && \
               cd ~/matrix-server && docker-compose start nginx && \
               docker-compose restart coturn"

# Log the renewal attempt
echo "Certificate renewal check completed at $(date)" >> $LOG_FILE
EOF

chmod +x scripts/renew-certs.sh

# Add to crontab (check twice daily)
(crontab -l 2>/dev/null; echo "0 */12 * * * ~/matrix-server/scripts/renew-certs.sh") | crontab -
```

### Key Rotation

```bash
cat > scripts/rotate-keys.sh << 'EOF'
#!/bin/bash

# Rotate TURN server secret
NEW_TURN_SECRET=$(openssl rand -base64 48)
sed -i "s/TURN_SECRET=.*/TURN_SECRET=$NEW_TURN_SECRET/" ~/matrix-server/.env

# Generate new media encryption keys
openssl genpkey -algorithm kyber1024 -out ~/matrix-server/conduit/config/pqc_media.key.new
openssl pkey -pubout -in ~/matrix-server/conduit/config/pqc_media.key.new -out ~/matrix-server/conduit/config/pqc_media.pub.new
mv ~/matrix-server/conduit/config/pqc_media.key.new ~/matrix-server/conduit/config/pqc_media.key
mv ~/matrix-server/conduit/config/pqc_media.pub.new ~/matrix-server/conduit/config/pqc_media.pub

# Restart services
cd ~/matrix-server
docker-compose restart conduit coturn

echo "Keys rotated at $(date)"
EOF

chmod +x scripts/rotate-keys.sh

# Add to crontab (quarterly rotation)
(crontab -l 2>/dev/null; echo "0 4 1 */3 * ~/matrix-server/scripts/rotate-keys.sh") | crontab -
```

### Advanced Backup Strategy with Rclone and Borg

First, install Rclone and Borg Backup:

```bash
# Install rclone
curl https://rclone.org/install.sh | sudo bash

# Install borgbackup
sudo apt-get update
sudo apt-get install -y borgbackup

# Create configuration directories
mkdir -p ~/.config/rclone ~/.config/borg
```

#### Configure Rclone

```bash
cat > scripts/setup-rclone.sh << 'EOF'
#!/bin/bash

# Interactive Rclone configuration
echo "Setting up Rclone remote for backups..."
echo "We'll configure a new remote storage. Follow the prompts."
echo "-------------------------"
echo "Recommended options:"
echo "- For local backups: Choose 'local' type"
echo "- For cloud storage: Choose your provider (S3, Google Drive, etc.)"
echo "-------------------------"

rclone config

# Test the configuration
echo "Testing rclone configuration..."
REMOTE_NAME=$(rclone listremotes | head -n 1)
if [ -z "$REMOTE_NAME" ]; then
    echo "No remote found! Please run 'rclone config' manually to set up a remote."
    exit 1
fi

# Create backup directory in remote
BACKUP_DIR="matrix-backups"
rclone mkdir "${REMOTE_NAME}${BACKUP_DIR}"
echo "Created backup directory: ${REMOTE_NAME}${BACKUP_DIR}"

# Save the remote name for later use
echo "REMOTE_NAME=\"$REMOTE_NAME\"" > ~/.config/rclone/matrix_backup_config
echo "BACKUP_DIR=\"$BACKUP_DIR\"" >> ~/.config/rclone/matrix_backup_config
EOF

chmod +x scripts/setup-rclone.sh
./scripts/setup-rclone.sh
```

#### Configure Borg Backup with Retention Policy

```bash
cat > scripts/setup-borg.sh << 'EOF'
#!/bin/bash

# Source Rclone configuration
source ~/.config/rclone/matrix_backup_config

# Variables
BORG_REPO=~/matrix-borg-repo
BORG_PASSPHRASE=$(openssl rand -base64 32)

# Initialize Borg repository
mkdir -p $BORG_REPO
borg init --encryption=repokey $BORG_REPO

# Save the passphrase securely
echo "BORG_PASSPHRASE=\"$BORG_PASSPHRASE\"" > ~/.config/borg/matrix_backup_config
chmod 600 ~/.config/borg/matrix_backup_config

echo "Borg repository initialized at $BORG_REPO"
echo "IMPORTANT: Your repository passphrase has been saved to ~/.config/borg/matrix_backup_config"
echo "Keep this passphrase in a safe place or you won't be able to restore your backups!"
EOF

chmod +x scripts/setup-borg.sh
./scripts/setup-borg.sh
```

#### Create Automatic Backup Script with Retention Policy

```bash
cat > scripts/backup.sh << 'EOF'
#!/bin/bash

# Source configuration files
source ~/.config/rclone/matrix_backup_config
source ~/.config/borg/matrix_backup_config
export BORG_PASSPHRASE

# Variables
BORG_REPO=~/matrix-borg-repo
TIMESTAMP=$(date +%Y%m%d-%H%M)
LOG_FILE=~/matrix-server/logs/backup.log
mkdir -p ~/matrix-server/logs

# Function for logging
log() {
    echo "$(date +'%Y-%m-%d %H:%M:%S') - $1" | tee -a $LOG_FILE
}

log "Starting Matrix server backup..."

# Stop services for clean backup
cd ~/matrix-server
docker-compose stop conduit
log "Services stopped for backup"

# Create Borg backup
log "Restoring backup $BACKUP_NAME to $RESTORE_DIR..."
borg create --stats --compression zlib,6 \
    $BORG_REPO::matrix-$TIMESTAMP \
    ~/matrix-server/conduit/data \
    ~/matrix-server/conduit/config \
    ~/matrix-server/keycloak/data \
    ~/matrix-server/postgres/data \
    ~/matrix-server/coturn/data \
    ~/matrix-server/.env
BACKUP_STATUS=$?

# Restart services
docker-compose start conduit
log "Services restarted"

# Check backup status
if [ $BACKUP_STATUS -ne 0 ]; then
    log "ERROR: Backup creation failed with status $BACKUP_STATUS"
    exit 1
fi

log "Borg backup created successfully"

# Apply retention policy
# Keep all backups from the last 7 days
# Keep one backup per day from last 15 days
# Keep one backup per week from last 30 days
# Keep one backup per month from last 60 days
borg prune -v --list $BORG_REPO \
    --keep-within=7d \
    --keep-daily=15 \
    --keep-weekly=4 \
    --keep-monthly=2
PRUNE_STATUS=$?

if [ $PRUNE_STATUS -ne 0 ]; then
    log "WARNING: Borg prune returned status $PRUNE_STATUS"
fi

log "Retention policy applied"

# Sync to remote storage
log "Syncing backups to remote storage..."
rclone sync $BORG_REPO ${REMOTE_NAME}${BACKUP_DIR}/borg-repo
SYNC_STATUS=$?

if [ $SYNC_STATUS -ne 0 ]; then
    log "ERROR: Rclone sync failed with status $SYNC_STATUS"
else
    log "Remote backup completed successfully"
fi

# Cleanup old remote backups (anything older than 60 days)
log "Cleaning up old remote backups (>60 days)..."
CUTOFF_DATE=$(date -d "60 days ago" +%Y%m%d)
rclone delete --min-age 60d ${REMOTE_NAME}${BACKUP_DIR}/borg-repo

log "Backup process completed"
EOF

chmod +x scripts/backup.sh

# Add to crontab (twice daily backups)
(crontab -l 2>/dev/null; echo "0 */12 * * * ~/matrix-server/scripts/backup.sh") | crontab -
```

#### Test and Restore Script

```bash
cat > scripts/restore.sh << 'EOF'
#!/bin/bash

# Source Borg configuration
source ~/.config/borg/matrix_backup_config
export BORG_PASSPHRASE

# Variables
BORG_REPO=~/matrix-borg-repo
RESTORE_DIR=~/matrix-restore
LOG_FILE=~/matrix-server/logs/restore.log
mkdir -p ~/matrix-server/logs
mkdir -p $RESTORE_DIR

# Function for logging
log() {
    echo "$(date +'%Y-%m-%d %H:%M:%S') - $1" | tee -a $LOG_FILE
}

# List available backups
log "Available backups:"
borg list $BORG_REPO | tee -a $LOG_FILE

# Get backup to restore
echo "Enter the name of the backup to restore (e.g., matrix-20250228-1200):"
read BACKUP_NAME

# Check if backup exists
if ! borg list $BORG_REPO | grep -q "$BACKUP_NAME"; then
    log "ERROR: Backup $BACKUP_NAME not found!"
    exit 1
fi

# Stop services
log "Stopping Matrix services..."
cd ~/matrix-server
docker-compose down

# Restore backup
log "Restoring backup $BACKUP_NAME to $RESTORE_DIR..."
borg extract $BORG_REPO::$BACKUP_NAME -p
RESTORE_STATUS=$?

if [ $RESTORE_STATUS -ne 0 ]; then
    log "ERROR: Restore failed with status $RESTORE_STATUS"
    exit 1
fi

log "Backup extracted successfully. Please move the restored files to their proper locations."
log "After verification, restart the services with: docker-compose up -d"
EOF

chmod +x scripts/restore.sh
```

## 🔍 Monitoring & Health Checks

Set up basic monitoring with Prometheus and Grafana (optional):

```bash
# Add to docker-compose.yml
cat >> docker-compose.yml << 'EOF'

  # Prometheus for monitoring
  prometheus:
    image: prom/prometheus
    container_name: prometheus
    restart: unless-stopped
    volumes:
      - ./prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - matrix-net

  # Grafana for dashboards
  grafana:
    image: grafana/grafana
    container_name: grafana
    restart: unless-stopped
    volumes:
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"
    networks:
      - matrix-net
    depends_on:
      - prometheus

volumes:
  prometheus_data:
  grafana_data:
EOF

# Create Prometheus config
mkdir -p prometheus
cat > prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'conduit'
    static_configs:
      - targets: ['conduit:6167']
    metrics_path: '/_matrix/metrics'

  - job_name: 'coturn'
    static_configs:
      - targets: ['coturn:9641']
EOF

# Update services
docker-compose up -d prometheus grafana
```

## ❓ Troubleshooting

### Common Issues and Solutions

#### 1. ICE Negotiation Failures in Calls

```bash
# Check TURN server connectivity
nc -zv turn.yourdomain.com 3478  # UDP
nc -zv turn.yourdomain.com 5349  # TCP/TLS

# Check TURN server logs
docker logs coturn

# Verify firewall settings
sudo ufw status
# Ensure ports 3478/UDP, 5349/TCP are open
```

#### 2. Database Encryption Issues

```bash
# Check for database corruption
docker exec -it conduit conduit-admin check-db

# Backup and reset if needed
docker-compose stop conduit
cp -r ~/matrix-server/conduit/data ~/matrix-server/conduit/data.bak
# Then restart
docker-compose start conduit
```

#### 3. Storj Connection Problems

```bash
# Test Storj connectivity
uplink ls sj://matrix-media

# Check credentials
docker exec -it conduit cat /etc/matrix-conduit/conduit.toml | grep storj

# Verify network access from Docker container
docker exec -it conduit ping gateway.storjshare.io
```

#### 4. SSL Certificate Issues

```bash
# Check certificate validity
openssl x509 -in ~/matrix-server/certs/fullchain.pem -text -noout | grep "Not After"

# Test TLS connection
openssl s_client -connect yourdomain.com:443 -tls1_3

# Force certificate renewal
sudo certbot renew --force-renewal
~/matrix-server/scripts/renew-certs.sh
```

## 📊 Performance Monitoring

Set up basic monitoring with Prometheus and Grafana (optional):

```bash
# Add to docker-compose.yml
cat >> docker-compose.yml << 'EOF'

  # Prometheus for monitoring
  prometheus:
    image: prom/prometheus
    container_name: prometheus
    restart: unless-stopped
    volumes:
      - ./prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - matrix-net

  # Grafana for dashboards
  grafana:
    image: grafana/grafana
    container_name: grafana
    restart: unless-stopped
    volumes:
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"
    networks:
      - matrix-net
    depends_on:
      - prometheus

volumes:
  prometheus_data:
  grafana_data:
EOF

# Create Prometheus config
mkdir -p prometheus
cat > prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'conduit'
    static_configs:
      - targets: ['conduit:6167']
    metrics_path: '/_matrix/metrics'

  - job_name: 'coturn'
    static_configs:
      - targets: ['coturn:9641']
EOF

# Update services
docker-compose up -d prometheus grafana
```

## 🌟 Additional Resources

- [Matrix Documentation](https://matrix.org/docs/)
- [Conduit GitHub Repository](https://github.com/matrix-org/conduit)
- [Element Client Documentation](https://element.io/get-started)
- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [Storj Documentation](https://docs.storj.io/)

## ⚠️ Security Best Practices

1. Regularly update all components with `docker-compose pull && docker-compose up -d`
2. Use strong, unique passwords for all services
3. Rotate encryption keys quarterly
4. Monitor logs for suspicious activity
5. Keep all certificates up to date with frequent renewal checks
6. Implement IP-based rate limiting at the nginx level
7. Enable fail2ban to prevent brute force attempts
8. Follow backup 3-2-1 rule: 3 copies of data, 2 different storage types, 1 offsite backup
9. Encrypt all backups with post-quantum algorithms
10. Regularly test the restoration process

### Automated Security Checks

```bash
cat > scripts/security-check.sh << 'EOF'
#!/bin/bash

# Variables
LOG_FILE=~/matrix-server/logs/security-check.log
mkdir -p ~/matrix-server/logs

# Function for logging
log() {
    echo "$(date +'%Y-%m-%d %H:%M:%S') - $1" | tee -a $LOG_FILE
}

log "Starting security audit..."

# Check SSL certificate expiry
DOMAIN="yourdomain.com"
CERT_EXPIRY=$(openssl x509 -enddate -noout -in ~/matrix-server/certs/fullchain.pem | cut -d= -f2)
CERT_EXPIRY_EPOCH=$(date -d "$CERT_EXPIRY" +%s)
CURRENT_EPOCH=$(date +%s)
DAYS_REMAINING=$(( ($CERT_EXPIRY_EPOCH - $CURRENT_EPOCH) / 86400 ))

log "SSL certificate expires in $DAYS_REMAINING days"
if [ $DAYS_REMAINING -lt 15 ]; then
    log "WARNING: Certificate expiring soon!"
fi

# Check Docker container updates
log "Checking for container updates..."
cd ~/matrix-server
UPDATES_NEEDED=$(docker-compose pull | grep -c "Image up to date")
if [ $UPDATES_NEEDED -gt 0 ]; then
    log "Some containers have updates available. Consider running docker-compose up -d"
fi

# Check for exposed ports
log "Checking for unnecessary exposed ports..."
EXPOSED_PORTS=$(sudo netstat -tulpn | grep LISTEN)
echo "$EXPOSED_PORTS" >> $LOG_FILE
# Check specifically for Matrix-related ports
echo "$EXPOSED_PORTS" | grep -E '(8455|5349|3478)' >> $LOG_FILE

# Check disk space for backups
DISK_SPACE=$(df -h | grep "/dev/sda1")
log "Disk space: $DISK_SPACE"

# Check fail2ban status
if command -v fail2ban-client &> /dev/null; then
    FAIL2BAN_STATUS=$(sudo fail2ban-client status)
    log "Fail2ban status: $FAIL2BAN_STATUS"
else
    log "WARNING: fail2ban not installed!"
fi

# Check firewall status
if command -v ufw &> /dev/null; then
    UFW_STATUS=$(sudo ufw status)
    log "Firewall status: $UFW_STATUS"
else
    log "WARNING: ufw not installed or not configured!"
fi

log "Security audit completed"
EOF

chmod +x scripts/security-check.sh

# Add to crontab (daily security checks)
(crontab -l 2>/dev/null; echo "0 1 * * * ~/matrix-server/scripts/security-check.sh") | crontab -
```

## 🤝 Contributing

Feel free to submit pull requests or open issues if you have suggestions for improvements!

## 📜 License

This project is available under the MIT License.

## One-Command Deployment

To deploy on any Ubuntu server:

```bash
curl -sSL https://raw.githubusercontent.com/yourusername/pq-matrix/main/install.sh | bash
```

## GitHub Repository Setup

1. Create new repository at https://github.com/new
2. Push local files:
```bash
git remote add origin https://github.com/yourusername/pq-matrix.git
git branch -M main
git push -u origin main
```

Follow these instructions to make the following change to my code document.

Instruction: Update README with comprehensive documentation of all new security features

Code Edit:
```
# 🛡️ PQ Matrix Ecosystem - Quantum-Resistant Deployment

A fully automated, single-command deployment system for quantum-resistant secure infrastructure with military-grade security and state-sponsored hacker protection.

## 🔐 Security Features

- **Post-Quantum Cryptography**
  - ✅ Kyber-1024 NIST-standardized encryption
  - ✅ BLS12-381 signatures for threshold cryptography
  - ✅ Hybrid classical+quantum-resistant encryption
  - ✅ Memory-safe implementation with zero-knowledge proofs

- **Hardware Security Module Integration**
  - ✅ YubiHSM 2 with FIPS 140-3 Level 3 compliance
  - ✅ Quantum-safe key storage and operations
  - ✅ Tamper-resistant cryptographic boundary
  - ✅ Hardware-enforced key isolation

- **Distributed Trust Protocol**
  - ✅ Threshold cryptography (3-of-5 signature scheme)
  - ✅ Geographic shard distribution across major cloud providers
  - ✅ Multi-region key storage for enhanced security
  - ✅ IETF DSKE protocol implementation

- **Zero-Logs Policy**
  - ✅ Memory-mapped secure audit logs with Shake-256 hashing
  - ✅ No persistent storage of sensitive information
  - ✅ Ephemeral cryptographic operations
  - ✅ Tamper-evident audit trail

- **Additional Security Measures**
  - ✅ CIS Level 2 server hardening
  - ✅ Cloudflare Zero Trust integration
  - ✅ Atomic operations with automatic rollback
  - ✅ End-to-end TLS with quantum-resistant ciphers

## ⚡ One-Command Deployment

```bash
curl -sSL https://raw.githubusercontent.com/MNylif/PQ-Matrix-Installer/main/install.sh | bash
```

This single command:
1. Installs all required system dependencies
2. Sets up Python virtual environment
3. Configures rclone with encrypted storage
4. Establishes Borg backup system
5. Integrates with Cloudflare API
6. Applies comprehensive server hardening
7. Implements quantum-resistant key management

## 🚀 Deployment Phases

The deployment process is modular and secure:

### Phase 1: Initial Setup
- Collects necessary configuration information
- Validates system compatibility
- Establishes secure credential storage

### Phase 2: Rclone Configuration
- Sets up encrypted cloud storage
- Implements quantum-resistant key management
- Validates connection and permissions

### Phase 3: Borg Backup
- Configures secure backup repository
- Implements quantum-resistant encryption
- Sets up scheduled backup jobs

### Phase 4: Cloudflare Integration
- Automates DNS management
- Configures Zero Trust access policies
- Enables quantum-safe TLS connections

### Phase 5: Server Hardening
- Applies CIS Level 2 benchmarks
- Configures firewall and intrusion detection
- Implements kernel security enhancements

## 🛠️ Technical Architecture

### Hardware Security Module
The system integrates with hardware security modules via:
```python
class QuantumHSM:
    def __init__(self):
        self.hsm = YubiHSM()
        self.session = self.hsm.create_session()
        # FIPS 140-3 Level 3 Configuration
        subprocess.run(
            "yubihsm-shell --command='config fips-mode enable'",
            shell=True,
            check=True
        )
```

### Distributed Trust Implementation
Keys are split across geographic regions using threshold cryptography:
```bash
class DistributedTrust:
    def __init__(self, shares=5, threshold=3):
        self.dkg = DistributedKeyGenerator(
            participants=shares,
            threshold=threshold,
            algorithm='bls12-381'
        )
```

### Zero-Logs Policy
Memory-safe logging with no persistent storage:
```bash
class SecureLogger:
    def __init__(self):
        self.buffer = mmap.mmap(-1, 1024)
        
    def write(self, data: str):
        hashed = hashlib.shake_256(data.encode()).hexdigest(64)
        self.buffer.seek(0)
        self.buffer.write(hashed.encode())
        
    def flush(self):
        self.buffer.seek(0)
        self.buffer.write(b'\0'*1024)
```

## 📋 Requirements

- Ubuntu 20.04+ or Debian-based system
- Python 3.8+
- Internet connectivity
- Administrative privileges

## 🔧 Recommended Hardware

- CPU: 4+ cores
- RAM: 8GB+
- Storage: 100GB+ SSD
- Optional: Hardware Security Module (YubiHSM 2)

## ⚠️ Security Considerations

1. **Physical Security**: For maximum security, deploy on hardware with secure boot and TPM.
2. **Key Management**: Store recovery keys in secure, separate locations.
3. **Regular Audits**: Periodically verify the integrity of your deployment.
4. **Geographic Distribution**: For critical applications, use multi-region HSM deployments.

## 🔄 Ongoing Maintenance

- **Key Rotation**: Automatic quarterly rotation of cryptographic keys
- **Security Updates**: Continuous integration of post-quantum algorithm updates
- **Compliance Checks**: Regular validation against FIPS 140-3 standards

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.