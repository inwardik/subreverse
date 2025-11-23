# Traefik Reverse Proxy Setup Guide

This guide explains how to set up Traefik as a shared reverse proxy for multiple projects on your server.

## Overview

Previously, SubReverse used its own nginx container for reverse proxying. Now, we use a **shared Traefik instance** that can handle multiple projects on the same server. This approach:

- ✅ Centralizes SSL certificate management
- ✅ Simplifies routing configuration
- ✅ Automatically discovers new services via Docker labels
- ✅ Provides automatic Let's Encrypt SSL certificates
- ✅ Allows multiple projects to coexist on the same server

## Architecture

```
                                    ┌─────────────────┐
                                    │                 │
Internet ──────────────────────────▶│    Traefik      │
 (ports 80/443)                     │  (Reverse Proxy)│
                                    │                 │
                                    └────────┬────────┘
                                             │
                          ┌──────────────────┼──────────────────┐
                          │                  │                  │
                          ▼                  ▼                  ▼
                   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
                   │  SubReverse  │   │Another Project│   │ Project 3... │
                   │subreverse.fun│   │another_pr.fun │   │              │
                   └──────────────┘   └──────────────┘   └──────────────┘
```

## Step 1: Install Traefik (One-time setup)

### 1.1 Create Traefik directory

```bash
# Create a dedicated directory for Traefik
sudo mkdir -p /opt/traefik
cd /opt/traefik

# Create directory for Let's Encrypt certificates
mkdir -p letsencrypt
```

### 1.2 Create docker-compose.yml

Copy the example configuration:

```bash
# From the SubReverse repository
cp /path/to/subreverse/traefik-compose.example.yml /opt/traefik/docker-compose.yml
```

Or create `/opt/traefik/docker-compose.yml` manually:

```yaml
version: '3.8'

services:
  traefik:
    image: traefik:v2.10
    container_name: traefik
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    ports:
      - "80:80"
      - "443:443"
      # Dashboard (optional, comment out in production)
      - "8080:8080"
    environment:
      - LETSENCRYPT_EMAIL=your-email@example.com
    command:
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--providers.docker.network=traefik-public"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.email=${LETSENCRYPT_EMAIL}"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
      - "--api.dashboard=true"
      - "--api.insecure=true"
      - "--log.level=INFO"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./letsencrypt:/letsencrypt
    networks:
      - traefik-public
    labels:
      - "traefik.enable=true"
      - "traefik.http.middlewares.redirect-to-https.redirectscheme.scheme=https"
      - "traefik.http.middlewares.redirect-to-https.redirectscheme.permanent=true"

networks:
  traefik-public:
    external: true
```

### 1.3 Update configuration

Edit the `docker-compose.yml` file:

```bash
nano /opt/traefik/docker-compose.yml
```

**IMPORTANT**: Change `your-email@example.com` to your actual email address for Let's Encrypt notifications.

### 1.4 Create the external network

```bash
docker network create traefik-public
```

### 1.5 Start Traefik

```bash
cd /opt/traefik
docker-compose up -d
```

### 1.6 Verify Traefik is running

```bash
# Check container status
docker ps | grep traefik

# Check logs
docker logs traefik

# Access dashboard (if enabled)
# Open http://your-server-ip:8080 in browser
```

## Step 2: Configure SubReverse Project

### 2.1 Update docker-compose.yml

The SubReverse `docker-compose.yml` has been updated with Traefik labels. Key changes:

1. **Removed nginx service** (no longer needed)
2. **Added Traefik labels** to `backend` and `frontend` services
3. **Added traefik-public network** (external network shared with Traefik)
4. **Changed ports to expose** (instead of publishing to host)

### 2.2 Start SubReverse

```bash
cd /home/user/subreverse
docker-compose up -d
```

Traefik will automatically:
- Detect the containers via Docker labels
- Route traffic based on `Host()` rules
- Request and configure SSL certificates from Let's Encrypt
- Redirect HTTP to HTTPS

### 2.3 DNS Configuration

Make sure your domain points to your server:

```bash
# Check DNS resolution
dig subreverse.fun
nslookup subreverse.fun
```

Your DNS should have an A record pointing to your server's IP:

```
subreverse.fun.  IN  A  <your-server-ip>
```

### 2.4 Verify

```bash
# Check that containers are on the traefik-public network
docker network inspect traefik-public

# Test HTTP redirect
curl -I http://subreverse.fun

# Test HTTPS
curl -I https://subreverse.fun
```

## Step 3: Add Another Project

To add a new project (e.g., `another_project` at `https://another_project.fun`):

### 3.1 Create project directory

```bash
mkdir -p /home/user/another_project
cd /home/user/another_project
```

### 3.2 Add Traefik labels to docker-compose.yml

Example for a simple web application:

```yaml
version: '3.8'

services:
  web:
    image: nginx:alpine
    container_name: another_project_web
    restart: unless-stopped
    expose:
      - "80"
    networks:
      - traefik-public
    labels:
      - "traefik.enable=true"
      - "traefik.docker.network=traefik-public"

      # HTTPS router
      - "traefik.http.routers.another-project.rule=Host(`another_project.fun`)"
      - "traefik.http.routers.another-project.entrypoints=websecure"
      - "traefik.http.routers.another-project.tls=true"
      - "traefik.http.routers.another-project.tls.certresolver=letsencrypt"
      - "traefik.http.services.another-project.loadbalancer.server.port=80"

      # HTTP to HTTPS redirect
      - "traefik.http.routers.another-project-http.rule=Host(`another_project.fun`)"
      - "traefik.http.routers.another-project-http.entrypoints=web"
      - "traefik.http.routers.another-project-http.middlewares=redirect-to-https"

networks:
  traefik-public:
    external: true
```

### 3.3 Start the project

```bash
docker-compose up -d
```

Traefik will automatically detect the new container and configure routing + SSL!

## Traefik Label Reference

Here are the key Traefik labels used in SubReverse:

### Basic Configuration

```yaml
labels:
  # Enable Traefik for this container
  - "traefik.enable=true"

  # Specify which network Traefik should use to connect
  - "traefik.docker.network=traefik-public"
```

### Router Configuration (HTTPS)

```yaml
  # Router name: subreverse-frontend
  # Match requests to subreverse.fun
  - "traefik.http.routers.subreverse-frontend.rule=Host(`subreverse.fun`)"

  # Use the 'websecure' entrypoint (port 443)
  - "traefik.http.routers.subreverse-frontend.entrypoints=websecure"

  # Enable TLS
  - "traefik.http.routers.subreverse-frontend.tls=true"

  # Use Let's Encrypt for SSL certificates
  - "traefik.http.routers.subreverse-frontend.tls.certresolver=letsencrypt"

  # Priority (higher number = checked first)
  # Backend has priority 10, frontend has priority 1
  - "traefik.http.routers.subreverse-frontend.priority=1"
```

### Service Configuration

```yaml
  # Specify which port Traefik should forward traffic to
  - "traefik.http.services.subreverse-frontend.loadbalancer.server.port=5173"
```

### HTTP to HTTPS Redirect

```yaml
  # HTTP router (same host rule)
  - "traefik.http.routers.subreverse-frontend-http.rule=Host(`subreverse.fun`)"

  # Use 'web' entrypoint (port 80)
  - "traefik.http.routers.subreverse-frontend-http.entrypoints=web"

  # Apply redirect middleware
  - "traefik.http.routers.subreverse-frontend-http.middlewares=redirect-to-https"
```

### Path-based Routing (Backend API)

```yaml
  # Match specific paths (API endpoints)
  - "traefik.http.routers.subreverse-backend.rule=Host(`subreverse.fun`) && (PathPrefix(`/api`) || PathPrefix(`/auth`) || PathPrefix(`/health`))"

  # Higher priority to match before frontend catch-all
  - "traefik.http.routers.subreverse-backend.priority=10"
```

## Common Tasks

### View Traefik Dashboard

If the dashboard is enabled (port 8080):

```bash
# Open in browser
http://your-server-ip:8080
```

**Security Note**: In production, either disable the dashboard or protect it with authentication.

### Check SSL Certificates

```bash
# View certificate details
docker exec traefik cat /letsencrypt/acme.json | jq

# Test SSL configuration
curl -vI https://subreverse.fun 2>&1 | grep -i 'ssl\|tls'
```

### View Traefik Logs

```bash
# Real-time logs
docker logs -f traefik

# Last 100 lines
docker logs --tail 100 traefik
```

### Restart Traefik

```bash
cd /opt/traefik
docker-compose restart
```

### Update Traefik

```bash
cd /opt/traefik
docker-compose pull
docker-compose up -d
```

## Troubleshooting

### SSL Certificate Not Working

**Problem**: Site shows "Not Secure" or certificate errors

**Solutions**:

1. Check Let's Encrypt rate limits (5 certs per domain per week)
2. Verify DNS points to your server
3. Check Traefik logs: `docker logs traefik | grep acme`
4. Try Let's Encrypt staging server first (uncomment in traefik config):
   ```yaml
   - "--certificatesresolvers.letsencrypt.acme.caserver=https://acme-staging-v02.api.letsencrypt.org/directory"
   ```
5. Delete `letsencrypt/acme.json` and restart Traefik

### 404 Not Found

**Problem**: Traefik returns 404

**Solutions**:

1. Check container is on `traefik-public` network:
   ```bash
   docker network inspect traefik-public
   ```
2. Verify labels are correct:
   ```bash
   docker inspect <container_name> | grep -A 20 Labels
   ```
3. Check Traefik dashboard to see if route is registered
4. Ensure `traefik.enable=true` label is present

### Service Unreachable

**Problem**: Traefik can't connect to service

**Solutions**:

1. Verify container is running: `docker ps`
2. Check the port in `loadbalancer.server.port` matches exposed port
3. Ensure both Traefik and service are on same network
4. Check service logs for errors

### HTTP Redirect Loop

**Problem**: Browser shows "too many redirects"

**Solutions**:

1. Check you're not redirecting HTTPS to HTTPS
2. Verify entrypoints are correct (`web` for HTTP, `websecure` for HTTPS)
3. Don't apply redirect middleware to HTTPS router

## Production Checklist

Before going to production:

- [ ] Change `LETSENCRYPT_EMAIL` to your real email
- [ ] Disable Traefik dashboard or protect with authentication
- [ ] Set up automatic Docker container restart policies
- [ ] Configure log rotation
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Regular backups of `letsencrypt/acme.json`
- [ ] Use Let's Encrypt production server (not staging)
- [ ] Review security headers (HSTS, CSP, etc.)

## Additional Resources

- [Traefik Documentation](https://doc.traefik.io/traefik/)
- [Traefik Docker Provider](https://doc.traefik.io/traefik/providers/docker/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Docker Networks](https://docs.docker.com/network/)

## Summary

1. **One-time setup**: Install Traefik in `/opt/traefik` and create `traefik-public` network
2. **Per-project**: Add Traefik labels to your containers and connect to `traefik-public` network
3. **Automatic**: Traefik handles routing, SSL, and HTTP→HTTPS redirects automatically

That's it! Your projects will automatically get HTTPS and proper routing without managing nginx configs.
