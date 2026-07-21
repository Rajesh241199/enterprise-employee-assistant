#!/usr/bin/env bash

set -Eeuo pipefail


: "${EXPECTED_SHA:?EXPECTED_SHA is required}"


if [[ ! "$EXPECTED_SHA" =~ ^[0-9a-f]{40}$ ]]
then
    echo "EXPECTED_SHA must be a valid 40-character Git commit SHA."
    exit 1
fi


APP_DIR="/home/ubuntu/enterprise-employee-assistant"
INFRA_DIR="$APP_DIR/infra/aws-ec2"
BACKUP_DIR="/home/ubuntu/production-backups"

COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.ec2"

POSTGRES_CONTAINER="internal_employee_assistant_postgres_prod"
BACKEND_CONTAINER="internal_employee_assistant_backend_prod"
FRONTEND_CONTAINER="internal_employee_assistant_frontend_prod"


log() {
    printf '\n[%s] %s\n' \
        "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
        "$1"
}


show_failure_logs() {
    echo
    echo "Deployment failed. Recent backend logs:"

    docker logs \
        "$BACKEND_CONTAINER" \
        --tail 150 \
        2>&1 \
        || true

    echo
    echo "Recent frontend logs:"

    docker logs \
        "$FRONTEND_CONTAINER" \
        --tail 80 \
        2>&1 \
        || true
}


trap show_failure_logs ERR


if [[ "$(id -u)" -ne 0 ]]
then
    echo "This deployment script must run as root through AWS SSM."
    exit 1
fi


for required_command in \
    docker \
    git \
    curl \
    python3 \
    sudo
do
    if ! command -v "$required_command" >/dev/null 2>&1
    then
        echo "Required command is unavailable: $required_command"
        exit 1
    fi
done


if [[ ! -d "$APP_DIR/.git" ]]
then
    echo "Production repository was not found at $APP_DIR."
    exit 1
fi


if [[ ! -f "$INFRA_DIR/$COMPOSE_FILE" ]]
then
    echo "Production Compose file was not found."
    exit 1
fi


if [[ ! -f "$INFRA_DIR/$ENV_FILE" ]]
then
    echo "Production environment file was not found."
    exit 1
fi


log "Validating the production repository"


if ! sudo -u ubuntu -H \
    git -C "$APP_DIR" diff --quiet
then
    echo "Production repository contains modified tracked files."
    exit 1
fi


if ! sudo -u ubuntu -H \
    git -C "$APP_DIR" diff --cached --quiet
then
    echo "Production repository contains staged changes."
    exit 1
fi


PREVIOUS_SHA="$(
    sudo -u ubuntu -H \
        git -C "$APP_DIR" rev-parse HEAD
)"


log "Current production commit: $PREVIOUS_SHA"
log "Approved deployment commit: $EXPECTED_SHA"


sudo -u ubuntu -H \
    git -C "$APP_DIR" fetch origin main


REMOTE_MAIN_SHA="$(
    sudo -u ubuntu -H \
        git -C "$APP_DIR" rev -C "$APP_DIR" fetch origin main


REMOTE_MAIN_SHA="$(
    sudo -u ubuntu -H \
       -parse origin/main
)"


if [[ "$REMOTE_MAIN_SHA" != "$EXPECTED_SHA" ]]
then
    echo "The approved commit is not the current origin/main commit."
    echo "Current origin/main: $REMOTE_MAIN_SHA"
    echo "Approved commit:     $EXPECTED_SHA"
    exit 1
fi


log "Creating a pre-deployment database backup"


mkdir -p "$BACKUP_DIR"


BACKUP_FILE="$BACKUP_DIR/before-deploy-$(date -u '+%Y%m%d-%H%M%S').sql"


docker exec \
    "$POSTGRES_CONTAINER" \
    sh -c \
    'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
    > "$BACKUP_FILE"


if [[ ! -s "$BACKUP_FILE" ]]
then
    echo "The database backup is empty."
    rm -f "$BACKUP_FILE"
    exit 1
fi


chown ubuntu:ubuntu "$BACKUP_FILE"
chmod 600 "$BACKUP_FILE"


log "Database backup created: $BACKUP_FILE"


log "Checking out the approved commit"


sudo -u ubuntu -H \
    git -C "$APP_DIR" checkout main


sudo -u ubuntu -H \
    git -C "$APP_DIR" pull --ff-only origin main


DEPLOYED_SHA="$(
    sudo -u ubuntu -H \
        git -C "$APP_DIR" rev-parse HEAD
)"


if [[ "$DEPLOYED_SHA" != "$EXPECTED_SHA" ]]
then
    echo "Checked-out commit does not match the approved commit."
    exit 1
fi


cd "$INFRA_DIR"


log "Building production backend and frontend images"


docker compose \
    --env-file "$ENV_FILE" \
    -f "$COMPOSE_FILE" \
    build backend frontend


log "Ensuring database tables exist"


docker compose \
    --env-file "$ENV_FILE" \
    -f "$COMPOSE_FILE" \
    run --rm backend \
    python -m app.db.init_db


log "Running employee-buddy migration"


docker compose \
    --env-file "$ENV_FILE" \
    -f "$COMPOSE_FILE" \
    run --rm backend \
    python -m scripts.migrate_employee_buddy_to_profile


log "Running password-security migration"


docker compose \
    --env-file "$ENV_FILE" \
    -f "$COMPOSE_FILE" \
    run --rm backend \
    python -m scripts.migrate_password_security


log "Running audit-log migration"


docker compose \
    --env-file "$ENV_FILE" \
    -f "$COMPOSE_FILE" \
    run --rm backend \
    python -m scripts.migrate_audit_logs


log "Recreating application containers"


docker compose \
    --env-file "$ENV_FILE" \
    -f "$COMPOSE_FILE" \
    up -d \
    --no-deps \
    --force-recreate \
    backend frontend


log "Waiting for production readiness"


HEALTH_OK="false"


for attempt in $(seq 1 60)
do
    HEALTH_RESPONSE="$(
        curl \
            --insecure \
            --silent \
            --show-error \
            --max-time 10 \
            https://127.0.0.1/ready \
            2>/dev/null \
            || true
    )"

    if python3 - "$HEALTH_RESPONSE" <<'PY'
import json
import sys

try:
    payload = json.loads(sys.argv[1])
except (IndexError, json.JSONDecodeError):
    raise SystemExit(1)

services = payload.get("services", {})

if payload.get("status") != "ok":
    raise SystemExit(1)

if services.get("postgres") != "ok":
    raise SystemExit(1)

if services.get("qdrant") != "ok":
    raise SystemExit(1)
PY
    then
        HEALTH_OK="true"
        break
    fi

    echo "Readiness attempt $attempt/60 did not pass."
    sleep 5
done


if [[ "$HEALTH_OK" != "true" ]]
then
    echo "Production readiness validation failed."
    exit 1
fi


log "Production containers"


docker compose \
    --env-file "$ENV_FILE" \
    -f "$COMPOSE_FILE" \
    ps


log "Production deployment completed successfully"
log "Deployed commit: $DEPLOYED_SHA"
log "Pre-deployment commit: $PREVIOUS_SHA"
log "Backup: $BACKUP_FILE"