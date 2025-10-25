## hng-stage-two — Blue/Green Docker Compose example

This repository demonstrates a simple blue/green deployment pattern using Docker Compose and an Nginx front-end.

Services

- `blue` — application container mapped to host port 8081
- `green` — application container mapped to host port 8082
- `nginx` — Nginx reverse proxy mapped to host port 8080 that forwards traffic to the active upstream

Files

- `docker-compose.yaml` — defines the three services and the `app_network` bridge network.
- `nginx.conf.template` — Nginx configuration template used by the `nginx` service. The template expects environment variables to be substituted before Nginx starts.
- `.env.example` — example environment variables for local development. Copy this to `.env` and edit as needed.

Environment variables

```bash
cp .env.example .env
# edit .env to set BLUE_IMAGE, GREEN_IMAGE, ACTIVE_POOL, PORT, etc.
```

Key variables in `.env`:

- `BLUE_IMAGE` / `GREEN_IMAGE` — Docker images used for the blue/green app containers.
- `RELEASE_ID_BLUE` / `RELEASE_ID_GREEN` — release identifiers (passed into app containers as env vars).
- `PORT` — port the app listens on _inside_ the app container (this value is substituted into the Nginx template).
- `ACTIVE_POOL` — either `blue` or `green`. The `nginx` service uses this value at startup to decide which backend is primary.

How it works (current behavior)

- The `nginx` service runs a small startup command that substitutes environment variables into `nginx.conf.template` then starts Nginx. The compose command is:

	/bin/sh -c "envsubst '$$PORT' '$$ACTIVE_POOL' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf && nginx -g 'daemon off;'"

- That means the variables `${PORT}` and `${ACTIVE_POOL}` are replaced in the template before Nginx runs.

- The `nginx.conf.template` currently places the active server first using `${ACTIVE_POOL}` and attempts to compute the backup server with a shell expression. Note: envsubst replaces variables but does not execute shell command substitutions embedded in the template. See the "Notes & recommendations" section below for a safe approach.

Traffic flow

1. Client requests -> host port 8080 -> Nginx
2. Nginx proxies to the upstream backend using the primary server selected via `${ACTIVE_POOL}` and a configured backup server

Quickstart — run locally

1. Copy and edit environment variables:

```bash
cp .env.example .env
# edit .env
```

2. Start all services:

```bash
docker compose up -d
```

3. Visit the app at:

```
http://localhost:8080
```

4. View logs:

```bash
docker compose logs -f nginx
docker compose logs -f blue
docker compose logs -f green
```

5. Stop and remove containers:

```bash
docker compose down
```

Switching the active pool

To change which pool is primary (blue or green):

1. Update `ACTIVE_POOL` in your `.env` (set to `blue` or `green`).
2. Recreate the `nginx` service so the new environment value is picked up and the template is re-rendered. For example:

```bash
docker compose up -d --no-deps --force-recreate nginx
```

This recreates the `nginx` container with the updated `ACTIVE_POOL` and re-renders `nginx.conf` using `envsubst`.

Notes & recommendations

- The current `nginx.conf.template` includes a shell command substitution to compute the backup server name. envsubst itself only substitutes environment variables and will not execute command substitutions inside the template. Because of that, the safest options are:

	- Replace the shell expression with explicit variables such as `${ACTIVE_POOL}` and `${BACKUP_POOL}`, and set `BACKUP_POOL` in `.env` (or compute it in the compose command). Example: add BACKUP_POOL to `.env` and include it in the `envsubst` invocation.

	- Or modify the `nginx` start command to compute a `BACKUP_POOL` environment variable in the shell and pass it to envsubst. Example (inside the `nginx` service command):

		/bin/sh -c "BACKUP_POOL=$( [ \"$ACTIVE_POOL\" = \"blue\" ] && echo green || echo blue ); envsubst '\$PORT \$ACTIVE_POOL \$BACKUP_POOL' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf && nginx -g 'daemon off;'"

	Either approach ensures the final generated `nginx.conf` contains concrete server names (no unevaluated shell expressions).

- When you change `.env`, remember to recreate the `nginx` container (see the recreate command above). A simple `docker compose restart nginx` will not pick up changed environment variables.

Troubleshooting

- If Nginx cannot reach the app containers, confirm the `PORT` in `.env` matches the port the app inside the image listens on.
- Ensure Docker can pull the images named in `BLUE_IMAGE` and `GREEN_IMAGE` or that they exist locally.

Next steps / improvements

- Add a `BACKUP_POOL` variable or compute it in the `nginx` start command to avoid leaving shell expressions in the template.
- Add healthchecks to the app services and/or use an upstream health-check mechanism so failover is automatic.
- Add a helper script to flip active pool and reload Nginx atomically.

If you want, I can implement a safe template approach (compute BACKUP_POOL in the start command or add the variable to `.env`) and add a small helper script to flip and reload the proxy. Tell me which behavior you prefer and I will implement it.



