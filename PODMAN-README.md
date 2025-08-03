# Podman Pod Configuration for Local AI Stack

This directory contains the Podman configuration files converted from the original Docker Compose setup. All services run in a single Podman pod with Traefik as the reverse proxy.

## Files Overview

- `podman-pod.yaml` - Main Kubernetes YAML file defining the pod and all containers
- `podman-setup.sh` - Management script for the pod lifecycle
- `traefik/traefik.yml` - Traefik static configuration
- `traefik/dynamic.yml` - Traefik dynamic routing configuration

## Prerequisites

1. **Podman** installed and configured
2. **envsubst** utility (usually part of gettext package)
3. **Environment variables** configured in `.env` file

## Quick Start

1. **Setup directories and environment**:
   ```bash
   ./podman-setup.sh setup
   ```

2. **Configure environment variables**:
   Edit the `.env` file with your actual values (it will be created from `.env.example` if it doesn't exist).

3. **Start the pod**:
   ```bash
   ./podman-setup.sh start
   ```

4. **Setup Ollama models** (after the pod is running):
   ```bash
   ./podman-setup.sh ollama-setup
   ```

## Service Access

Once the pod is running, services are available at:

| Service | URL | Description |
|---------|-----|-------------|
| Traefik Dashboard | http://localhost:8090 | Reverse proxy management |
| n8n | http://localhost:5678 | Workflow automation |
| Open WebUI | http://localhost:3000 | Chat interface |
| Flowise | http://localhost:3001 | AI workflow builder |
| Langfuse | http://localhost:3002 | LLM observability |
| Ollama | http://localhost:11434 | LLM inference API |
| Qdrant | http://localhost:6333 | Vector database |
| SearXNG | http://localhost:8080 | Search engine |
| MinIO Console | http://localhost:9091 | Object storage |
| ClickHouse | http://localhost:8123 | Analytics database |

## Management Commands

```bash
# Setup directories and check environment
./podman-setup.sh setup

# Start the pod
./podman-setup.sh start

# Stop the pod
./podman-setup.sh stop

# Restart the pod
./podman-setup.sh restart

# Check pod status
./podman-setup.sh status

# View logs for a specific container
./podman-setup.sh logs <container-name>

# Setup Ollama models
./podman-setup.sh ollama-setup
```

## Key Differences from Docker Compose

### Networking
- **Docker Compose**: Services communicate using service names as hostnames
- **Podman Pod**: All containers share the same network namespace and communicate via `localhost`

### Volume Management
- **Docker Compose**: Named volumes managed by Docker
- **Podman Pod**: Host path volumes mapped to local directories under `volumes/`

### Reverse Proxy
- **Docker Compose**: Caddy with `network_mode: host`
- **Podman Pod**: Traefik running inside the pod with proper port mappings

### Profiles
- **Docker Compose**: Used profiles for GPU variants of Ollama
- **Podman Pod**: Single CPU version included (GPU support requires additional configuration)

## Environment Variables

Key environment variables that need to be configured in `.env`:

```bash
# Database
POSTGRES_PASSWORD=your_secure_password

# n8n
N8N_ENCRYPTION_KEY=your_encryption_key
N8N_USER_MANAGEMENT_JWT_SECRET=your_jwt_secret

# Flowise
FLOWISE_USERNAME=admin
FLOWISE_PASSWORD=your_password

# Langfuse
LANGFUSE_SALT=your_salt
ENCRYPTION_KEY=your_encryption_key
NEXTAUTH_SECRET=your_nextauth_secret
CLICKHOUSE_PASSWORD=your_clickhouse_password
MINIO_ROOT_PASSWORD=your_minio_password

# Hostnames (optional, for custom domains)
N8N_HOSTNAME=n8n.yourdomain.com
WEBUI_HOSTNAME=webui.yourdomain.com
FLOWISE_HOSTNAME=flowise.yourdomain.com
# ... etc
```

## Troubleshooting

### Pod Won't Start
1. Check if all required environment variables are set in `.env`
2. Ensure Podman is running: `podman system info`
3. Check for port conflicts: `netstat -tulpn | grep -E ':(3000|3001|3002|5678|6333|8080|11434)'`

### Container Logs
```bash
# View logs for a specific container
./podman-setup.sh logs <container-name>

# Available container names:
# flowise, open-webui, n8n, qdrant, postgres, redis, clickhouse, 
# minio, langfuse-web, langfuse-worker, searxng, ollama, traefik
```

### Database Connection Issues
- Ensure PostgreSQL is ready before dependent services start
- Check database credentials in `.env`
- Verify database is accessible: `podman exec -it local-ai-stack-postgres psql -U postgres`

### Volume Permissions
If you encounter permission issues:
```bash
# Fix volume permissions
sudo chown -R $USER:$USER volumes/
chmod -R 755 volumes/
```

## GPU Support

The current configuration uses the CPU version of Ollama. For GPU support:

1. **NVIDIA GPU**:
   ```yaml
   # Add to ollama container in podman-pod.yaml
   securityContext:
     privileged: true
   resources:
     limits:
       nvidia.com/gpu: 1
   ```

2. **AMD GPU**:
   ```yaml
   # Change ollama image and add devices
   image: ollama/ollama:rocm
   securityContext:
     privileged: true
   volumeMounts:
   - name: dev-kfd
     mountPath: /dev/kfd
   - name: dev-dri
     mountPath: /dev/dri
   ```

## Migration from Docker Compose

To migrate data from existing Docker Compose setup:

1. **Stop Docker Compose services**:
   ```bash
   docker-compose down
   ```

2. **Copy volume data**:
   ```bash
   # Example for PostgreSQL data
   docker run --rm -v local-ai-packaged_langfuse_postgres_data:/source -v $(pwd)/volumes/postgres:/dest alpine cp -r /source/. /dest/
   ```

3. **Update file paths** in configuration files if needed

4. **Start Podman pod**:
   ```bash
   ./podman-setup.sh start
   ```

## Limitations

1. **No Docker Compose profiles**: GPU variants need manual configuration
2. **No `extra_hosts`**: Use localhost for inter-container communication
3. **No `network_mode: host`**: Traefik uses explicit port mappings
4. **Health checks**: Converted to Kubernetes-style readiness probes where possible

## Contributing

When modifying the configuration:

1. Update `podman-pod.yaml` for container changes
2. Update `traefik/dynamic.yml` for routing changes
3. Update this README for documentation changes
4. Test with `./podman-setup.sh restart`
