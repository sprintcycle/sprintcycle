# Deployment Assets

This directory contains optional production deployment assets for SprintCycle.

## Nginx TLS reverse proxy

- `nginx/nginx.conf`: recommended external reverse proxy for a single HTTPS entrypoint
- `nginx/site.conf`: HTTP-only redirect + ACME challenge handler
- `nginx/tls.conf`: TLS hardening and security headers
- `nginx/proxy_headers.conf`: shared proxy headers for upstream services

## Recommended routing

- `/` → `frontend:80`
- `/api/` → `frontend:80` (Nginx inside the frontend container proxies to backend)
- `/.well-known/acme-challenge/` → webroot for certificate validation
- `https://sprintcycle.example.com` as the single public entrypoint

## TLS notes

- Terminate TLS at the edge proxy
- Mount certificate files into `/etc/nginx/tls/`
- Mount Certbot webroot into `/var/www/certbot/`
- Use Let’s Encrypt / Certbot or your platform’s certificate manager
- Keep `deploy/nginx/site.conf` and `deploy/nginx/tls.conf` as reusable snippets
