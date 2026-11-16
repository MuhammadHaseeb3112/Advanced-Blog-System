# Deploying Advanced Blog System (public demo)

For a Linux server with Docker that already runs a Caddy reverse proxy on
ports 80/443 and a shared Docker network called `edge`. The stack publishes no
ports of its own; Caddy reaches it as `blog-web:8000` (HTTP and WebSockets).

Five containers: `blog-web` (Daphne), `blog-celery` (worker), `blog-beat`
(scheduler), `blog-db` (PostgreSQL 16) and `blog-redis`. About 0.6 GB RAM and
2 GB disk in total. Works on x86-64 and ARM64.

## 1. Domain

Point a (sub)domain at the server, e.g. `mh-blog.duckdns.org`.

## 2. Get the code and configure

```bash
git clone https://github.com/MuhammadHaseeb3112/Advanced-Blog-System.git blog
cd blog
cp deploy/env.prod.example deploy/.env.prod
nano deploy/.env.prod        # SECRET_KEY, POSTGRES_PASSWORD, your domain
```

## 3. Start

```bash
docker network create edge 2>/dev/null || true
docker compose -p blog -f deploy/compose.prod.yml --env-file deploy/.env.prod up -d --build
docker compose -p blog -f deploy/compose.prod.yml --env-file deploy/.env.prod ps
```

On first start `blog-web` runs migrations, collects static files, sets the
site domain and, with `DEMO_MODE=True`, loads the demo data (`seed_demo`).

## 4. Add the site to Caddy

In the Caddyfile of the stack that owns ports 80/443:

```
blog.example.com {
	encode zstd gzip
	header {
		Strict-Transport-Security "max-age=31536000"
		-Server
	}
	reverse_proxy blog-web:8000
}
```

Reload that Caddy. It gets the HTTPS certificate by itself, and
`reverse_proxy` passes WebSocket upgrades through.

## 5. Nightly reset and backups

```bash
crontab -e
# 22:10 UTC: back up, 22:30 UTC: reset the demo data
10 22 * * * bash ~/blog/deploy/backup.sh >> ~/blog-backup.log 2>&1
30 22 * * * cd ~/blog && docker compose -p blog -f deploy/compose.prod.yml --env-file deploy/.env.prod exec -T blog-web python manage.py seed_demo --reset >> ~/blog-reset.log 2>&1
```

## Updating

```bash
cd ~/blog && bash deploy/deploy.sh
```

It pulls the new code, rebuilds, waits for the health check and for the site
through Caddy, and rolls back to the previous version if either fails.

## Automatic deploys (GitHub Actions)

After CI passes on `main`, `.github/workflows/deploy.yml` connects over SSH
and runs `deploy/deploy.sh`. Turn it on in **Settings → Secrets and
variables → Actions**:

| Kind | Name | Value |
|---|---|---|
| Secret | `DEPLOY_HOST` | the server's public IP |
| Secret | `DEPLOY_USER` | `ubuntu` |
| Secret | `DEPLOY_SSH_KEY` | a private key whose public key is in the server's `~/.ssh/authorized_keys` |
| Variable | `DEPLOY_ENABLED` | `true` |
| Variable | `DEPLOY_URL` | `https://mh-blog.duckdns.org` |

## What demo mode does

- The login page offers one-click Author and Reader logins.
- Sign-up, password reset, profile and password changes and Django's
  `/admin/` are off, so the shared demo accounts keep working.
- No email is sent (the console backend is used).
- Writing, editing, deleting, likes, comments and live notifications all work;
  the data resets every night.
