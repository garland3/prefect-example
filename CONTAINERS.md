# Running Prefect in Containers

This guide covers running the Prefect server, worker, and flows in Docker and Kubernetes.

---

## Docker

### Quick: Single Container

Run the Prefect server in a single Docker container:

```bash
docker run -d -p 4200:4200 prefecthq/prefect:3-python3.12 \
  prefect server start --host 0.0.0.0
```

UI is at http://localhost:4200. Point your local client at it:

```bash
export PREFECT_API_URL=http://localhost:4200/api
```

### Production: Docker Compose

For a production-like setup with PostgreSQL, Redis, background services, and a worker, use Docker Compose.

Create `docker-compose.yml`:

```yaml
services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_USER: prefect
      POSTGRES_PASSWORD: prefect
      POSTGRES_DB: prefect
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U prefect"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD-SHELL", "redis-cli ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  prefect-server:
    image: prefecthq/prefect:3-latest
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      PREFECT_API_DATABASE_CONNECTION_URL: postgresql+asyncpg://prefect:prefect@postgres:5432/prefect
      PREFECT_SERVER_API_HOST: 0.0.0.0
      PREFECT_MESSAGING_BROKER: prefect_redis.messaging
      PREFECT_MESSAGING_CACHE: prefect_redis.messaging
      PREFECT_REDIS_MESSAGING_HOST: redis
      PREFECT_REDIS_MESSAGING_PORT: 6379
      PREFECT_REDIS_MESSAGING_DB: 0
    command: prefect server start --no-services
    ports:
      - "4200:4200"

  prefect-services:
    image: prefecthq/prefect:3-latest
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      PREFECT_API_DATABASE_CONNECTION_URL: postgresql+asyncpg://prefect:prefect@postgres:5432/prefect
      PREFECT_MESSAGING_BROKER: prefect_redis.messaging
      PREFECT_MESSAGING_CACHE: prefect_redis.messaging
      PREFECT_REDIS_MESSAGING_HOST: redis
      PREFECT_REDIS_MESSAGING_PORT: 6379
      PREFECT_REDIS_MESSAGING_DB: 0
    command: prefect server services start

  prefect-worker:
    image: prefecthq/prefect:3-latest
    depends_on:
      prefect-server:
        condition: service_started
    environment:
      PREFECT_API_URL: http://prefect-server:4200/api
    command: prefect worker start --pool local-pool

volumes:
  postgres_data:
  redis_data:
```

Run it:

```bash
docker compose up -d
```

Verify:

```bash
docker compose ps
curl http://localhost:4200/api/health
```

### Building a Custom Flow Image

To bake your flow code into a Docker image:

```dockerfile
FROM prefecthq/prefect:3-python3.12

COPY example_flow.py /opt/prefect/flows/
COPY deploy_flow.py /opt/prefect/flows/

WORKDIR /opt/prefect/flows
```

Build and push:

```bash
docker build -t myregistry/my-prefect-flows:latest .
docker push myregistry/my-prefect-flows:latest
```

---

## Kubernetes

### Architecture

In Kubernetes, a typical Prefect deployment looks like this:

```
┌─────────────────────────────────────────────────┐
│  Kubernetes Cluster                             │
│                                                 │
│  ┌──────────────┐   ┌───────────────────────┐   │
│  │ Prefect      │   │ PostgreSQL            │   │
│  │ Server Pod   │──▶│ (StatefulSet/Service) │   │
│  └──────┬───────┘   └───────────────────────┘   │
│         │                                       │
│         │ polls                                  │
│  ┌──────┴───────┐                               │
│  │ Prefect      │   ┌───────────────────────┐   │
│  │ Worker Pod   │──▶│ Flow Run Pods         │   │
│  └──────────────┘   │ (created per run)     │   │
│                     └───────────────────────┘   │
└─────────────────────────────────────────────────┘
```

- The **server** manages state and serves the UI/API.
- The **worker** polls the server for scheduled runs and creates Kubernetes Jobs/Pods to execute them.
- Each **flow run** gets its own Pod, giving isolation and resource control.

### Prerequisites

- A Kubernetes cluster (minikube, kind, EKS, GKE, AKS, etc.)
- `kubectl` configured
- `helm` installed

### Step 1: Add the Prefect Helm Repo

```bash
helm repo add prefect https://prefecthq.github.io/prefect-helm
helm repo update
```

### Step 2: Create a Namespace

```bash
kubectl create namespace prefect
```

### Step 3: Deploy the Prefect Server

Create `server-values.yaml`:

```yaml
server:
  basicAuth:
    enabled: false
  # Uncomment to enable auth:
  # basicAuth:
  #   enabled: true
  #   existingSecret: server-auth-secret
```

Install:

```bash
helm install prefect-server prefect/prefect-server \
  --namespace prefect \
  -f server-values.yaml
```

Verify it's running:

```bash
kubectl get pods -n prefect
```

Port-forward to access the UI locally:

```bash
kubectl port-forward svc/prefect-server -n prefect 4200:4200
```

UI is now at http://localhost:4200.

### Step 4: Create a Kubernetes Work Pool

```bash
export PREFECT_API_URL=http://localhost:4200/api
prefect work-pool create k8s-pool --type kubernetes
```

### Step 5: Deploy a Worker

Create `worker-values.yaml`:

```yaml
worker:
  apiConfig: selfHostedServer
  config:
    workPool: k8s-pool
  selfHostedServerApiConfig:
    apiUrl: http://prefect-server.prefect.svc.cluster.local:4200/api
```

Install:

```bash
helm install prefect-worker prefect/prefect-worker \
  --namespace prefect \
  -f worker-values.yaml
```

Verify:

```bash
kubectl get pods -n prefect
# You should see both prefect-server-xxx and prefect-worker-xxx pods
```

### Step 6: Deploy and Run a Flow

Deploy with a Docker image that contains your flow code:

```python
from prefect import flow

@flow(log_prints=True)
def etl_pipeline(source_url: str = "https://api.example.com/data"):
    print(f"Running ETL for {source_url}")

if __name__ == "__main__":
    etl_pipeline.deploy(
        name="k8s-etl-deployment",
        work_pool_name="k8s-pool",
        image="myregistry/my-prefect-flows:latest",
    )
```

Run the deployment script (with `PREFECT_API_URL` still port-forwarded):

```bash
python deploy_k8s.py
```

Trigger a run:

```bash
prefect deployment run 'etl-pipeline/k8s-etl-deployment'
```

The worker creates a new Pod in the cluster to execute the flow. Watch it:

```bash
kubectl get pods -n prefect --watch
```

### Step 7: Using prefect.yaml (Alternative)

For CI/CD pipelines, you can define everything declaratively in a `prefect.yaml` file:

```yaml
name: flows
prefect-version: 3.0.0

build:
  - prefect_docker.deployments.steps.build_docker_image:
      id: build-image
      requires: prefect-docker>=0.4.0
      image_name: myregistry/my-prefect-flows
      tag: latest
      dockerfile: auto
      platform: linux/amd64

push:
  - prefect_docker.deployments.steps.push_docker_image:
      requires: prefect-docker>=0.4.0
      image_name: "{{ build-image.image_name }}"
      tag: "{{ build-image.tag }}"

pull:
  - prefect.deployments.steps.set_working_directory:
      directory: /opt/prefect/flows

deployments:
  - name: etl-deployment
    entrypoint: example_flow.py:etl_pipeline
    work_pool:
      name: k8s-pool
      job_variables:
        image: "{{ build-image.image }}"
```

Then deploy with:

```bash
prefect deploy --all
```

---

## Quick Reference

| What | Docker | Kubernetes |
|---|---|---|
| Server | `docker run prefecthq/prefect:3-latest` | `helm install prefect-server prefect/prefect-server` |
| Worker | Container in docker-compose | `helm install prefect-worker prefect/prefect-worker` |
| Flow runs | Same container or separate | Individual Pods per run |
| Database | SQLite (dev) or PostgreSQL | PostgreSQL (StatefulSet or external) |
| Scaling | Manual | HPA on workers, Pods per flow run |
| UI | http://localhost:4200 | `kubectl port-forward` or Ingress |
