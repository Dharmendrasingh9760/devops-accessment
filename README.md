# DevOps Engineer Assignment — Dockerized FastAPI + Postgres + Redis + NGINX

A small but production-shaped deployment: FastAPI app behind NGINX, backed by PostgreSQL and Redis, fully containerized, with CI/CD via GitHub Actions.

## Stack

- **FastAPI** — app logic + `/health` endpoint
- **PostgreSQL 16** — durable storage
- **Redis 7** — cache/counters
- **NGINX** — reverse proxy, TLS termination, rate limiting
- **Docker Compose** — orchestration
- **GitHub Actions** — CI/CD (build → push to GHCR → SSH deploy to VPS)

## Quick start (local)

```bash
git clone <this-repo>
cd devops-assignment
cp .env.example .env        # edit passwords as you like for local testing
docker compose up -d --build
curl http://localhost/health
curl http://localhost/visits
```

## Repository layout

```
.
├── app/                     # FastAPI application
│   ├── main.py
│   └── requirements.txt
├── Dockerfile                # app image (multi-stage, non-root)
├── docker-compose.yml         # full stack: app, db, redis, nginx, certbot
├── .env.example
├── nginx/
│   └── nginx.conf             # reverse proxy + commented HTTPS block
├── scripts/
│   ├── backup.sh
│   └── restore.sh
├── .github/workflows/
│   └── deploy.yml             # CI/CD pipeline
└── docs/
    ├── ARCHITECTURE.md        # + architecture.svg diagram
    ├── DEPLOYMENT.md          # full walkthrough, including SSL options
    ├── SECURITY.md            # firewall, fail2ban, hardening
    └── BACKUP.md               # backup/restart/logging/monitoring strategy
```

## Documentation map

| Doc | Covers |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System diagram, component roles, network design |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Step-by-step VPS deployment, SSL (with and without a domain), CI/CD secrets, rollback |
| [`docs/SECURITY.md`](docs/SECURITY.md) | Firewall, fail2ban, SSH hardening, container/app security |
| [`docs/BACKUP.md`](docs/BACKUP.md) | Backup/restore, restart strategy, logging, monitoring |

## Health check

`GET /health` checks both Postgres and Redis connectivity and returns `503` if either is down — used by Docker's `HEALTHCHECK`, and the natural target for an external uptime monitor.

## SSL

No domain yet? `docs/DEPLOYMENT.md` documents three options: stay on HTTP behind the firewall, use a self-signed cert, or use a Cloudflare Tunnel for a free HTTPS endpoint with zero open inbound ports. With a domain, it's Let's Encrypt via the included `certbot` service.

## Notes on scope

This was built to demonstrate the patterns evaluators are likely looking for (multi-service Compose stack, reverse proxy, CI/CD with secrets, health checks, backups, security basics) within the assignment's timeline, rather than to be a fully battle-tested production system. Each doc calls out explicitly what a real production rollout would add next (monitoring stack, log aggregation, true zero-downtime deploys, image vulnerability scanning).
