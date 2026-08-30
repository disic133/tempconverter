# tempconverter

A small Flask app that converts Celsius to Fahrenheit and logs each conversion to a
MySQL 8 database. This repository contains the application plus everything needed to
build it as a container and deploy it on Docker Swarm and OpenShift.

The running page displays the student and college taken from the `STUDENT` and
`COLLEGE` environment variables, and the app connects to the database as a **non-root**
user (`tempuser`).

## Layout

| Path | Purpose |
|---|---|
| `app.py`, `templates/`, `requirements.txt` | The Flask application |
| `Dockerfile` | Builds the OCI image (updates OS packages, exposes 5000/tcp, non-root) |
| `compose.yaml` | Local run with Podman (app + MySQL 8) |
| `stack.yml` | Docker Swarm deployment (simple orchestrator) |
| `openshift-template.yaml` | OpenShift Template (complex orchestrator) |
| `tests/` | `test_unit.py` (conversion logic), `test_integration.py` (route + DB) |
| `.github/workflows/ci.yml` | CI: unit + integration tests, then build & push |
| `.env.example` | Copy to `.env` and fill in secrets (git-ignored) |

## 1. Build and publish the image

```bash
podman build -t tempconverter:latest .
podman login docker.io
podman tag tempconverter:latest docker.io/<registry-user>/tempconverter:latest
podman push docker.io/<registry-user>/tempconverter:latest
```

The page title in `templates/index.html` is `TempConverter`. After the change,
publish the `:dev` tag as well:

```bash
podman build -t tempconverter:dev .
podman tag tempconverter:dev docker.io/<registry-user>/tempconverter:dev
podman push docker.io/<registry-user>/tempconverter:dev
```

## 2. Run locally with Podman

```bash
cp .env.example .env      # then edit .env
podman-compose up --build -d
# browse http://localhost:8080
```

Verify the app uses the non-root DB user:

```bash
podman exec -it tempconverter_db_1 \
  mysql -u tempuser -p"$MYSQL_PASSWORD" tempdb \
  -e "SELECT celsius, fahrenheit FROM temperature ORDER BY id DESC LIMIT 5;"
```

## 3. Tests

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/test_unit.py                 # no database needed
# integration test needs a reachable MySQL 8 and DB_* env vars set
pytest tests/test_integration.py
```

## 4. Deploy on Docker Swarm

```bash
# on the manager node, with the image already pushed
set -a; . ./.env; set +a
docker stack deploy -c stack.yml tempconverter
docker service ps tempconverter_app        # replicas land on different nodes
# reachable on port 80 of any node IP; scale:
docker service scale tempconverter_app=3   # needs a 3rd node (see note below)
```

## 5. Deploy on OpenShift

```bash
oc new-project tempconverter
oc process -f openshift-template.yaml \
  -p STUDENT="Your Name" -p COLLEGE="Your College" \
  -p IMAGE="docker.io/<registry-user>/tempconverter:dev" \
  -p DB_PASSWORD="change-me" | oc apply -f -
oc get pods -o wide                        # two app pods on different nodes
oc get route tempconverter                 # external URL on port 80
oc scale deployment/tempconverter --replicas=3
```

## Notes

- **Scaling to 3 replicas** with the strict "not on the same node" rule needs one
  schedulable node per replica. With only two nodes the third replica stays *Pending*;
  add a third node, or relax the rule (Swarm: raise `max_replicas_per_node`; OpenShift:
  use `preferredDuringSchedulingIgnoredDuringExecution`).
- **MySQL on OpenShift** uses `registry.redhat.io/rhel9/mysql-80` so it runs under the
  restricted (random-UID) security context. The community `mysql:8` image would need the
  `anyuid` SCC.
- **Secrets** are passed as environment variables / OpenShift Secrets here for simplicity;
  a production setup would use a managed secret store and TLS on port 443.
