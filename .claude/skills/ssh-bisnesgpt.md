---
name: ssh-bisnesgpt
description: Set up SSH access to the BisnesGPT server via Cloudflare tunnel. Use when the user says "setup ssh", "connect to server", "ssh bisnesgpt", "setup bisnesgpt", or wants remote access to the BisnesGPT server.
---

# SSH BisnesGPT Setup

Sets up secure SSH access to the BisnesGPT server (Ubuntu) through a Cloudflare tunnel. Works from anywhere — no VPN or local network required.

## Server Details
- Hostname: `ssh.jutateknologi.com` (Cloudflare tunnel)
- User: `firaz`
- OS: Ubuntu 24.04 LTS

## Steps

### 1. Check if cloudflared is installed

```bash
which cloudflared
```

If not installed:
```bash
brew install cloudflare/cloudflare/cloudflared
```

On Linux:
```bash
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared
```

### 2. Authenticate with Cloudflare Access

Run this — it opens a browser for login. The user must have their email whitelisted in the Cloudflare Access policy by Firaz.

```bash
cloudflared access login https://ssh.jutateknologi.com
```

### 3. Check for existing SSH key

```bash
ls ~/.ssh/id_ed25519.pub 2>/dev/null || ls ~/.ssh/id_rsa.pub 2>/dev/null
```

If no key exists, generate one:
```bash
ssh-keygen -t ed25519 -C "$(whoami)@$(hostname)" -f ~/.ssh/id_ed25519 -N ""
```

### 4. Configure SSH

Check if `~/.ssh/config` already has a `bisnesgpt-remote` entry:
```bash
grep -c "bisnesgpt-remote" ~/.ssh/config 2>/dev/null
```

If not found, append this config:
```
Host bisnesgpt-remote
  HostName ssh.jutateknologi.com
  User firaz
  IdentityFile ~/.ssh/id_ed25519
  ProxyCommand cloudflared access tcp --hostname %h
```

Use the Edit tool to append to `~/.ssh/config`, or create the file if it doesn't exist.

### 5. Copy SSH public key to server

Show the user their public key:
```bash
cat ~/.ssh/id_ed25519.pub
```

Tell the user:
> Send this public key to Firaz. He needs to add it to `~/.ssh/authorized_keys` on the server. Until then, you'll need the server password to connect.

### 6. Test the connection

```bash
ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new bisnesgpt-remote "echo 'Connected!' && hostname && uptime"
```

If it works, confirm setup is complete.

If it fails with timeout: the Cloudflare tunnel may not be running on the server, or the user's email isn't in the Access policy.

### 7. Summary

After successful setup, tell the user:
- **Connect anytime:** `ssh bisnesgpt-remote`
- **Server path:** `~/backend/bisnesgpt-server/`
- **PM2 processes:** `pm2 status` to see running services
- **Tunnel auth expires periodically** — re-run `cloudflared access login https://ssh.jutateknologi.com` if connection stops working
