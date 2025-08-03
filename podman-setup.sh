#!/bin/bash

# Podman Pod Setup Script for Local AI Stack
# This script sets up the necessary directories and manages the Podman pod

set -e

PROJECT_DIR="/home/gryom/Projects/local-ai-packaged"
VOLUMES_DIR="$PROJECT_DIR/volumes"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to create necessary directories
create_directories() {
    log_info "Creating volume directories..."
    
    mkdir -p "$VOLUMES_DIR"/{flowise,open-webui,n8n,qdrant,postgres,valkey,clickhouse,clickhouse-logs,minio,ollama}
    mkdir -p "$PROJECT_DIR"/{traefik,searxng,shared,n8n/backup}
    
    # Set proper permissions
    chmod 755 "$VOLUMES_DIR"/*
    chmod 755 "$PROJECT_DIR"/{traefik,searxng,shared}
    
    log_info "Directories created successfully"
}

# Function to check if .env file exists
check_env_file() {
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        log_warn ".env file not found. Please create one based on .env.example"
        if [ -f "$PROJECT_DIR/.env.example" ]; then
            log_info "Copying .env.example to .env..."
            cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
            log_warn "Please edit .env file with your actual values before starting the pod"
        fi
    fi
}

# Function to start the pod
start_pod() {
    log_info "Starting Local AI Stack pod..."
    
    # Load environment variables
    if [ -f "$PROJECT_DIR/.env" ]; then
        set -a
        source "$PROJECT_DIR/.env"
        set +a
    fi
    
    # Replace environment variables in the YAML file
    envsubst < "$PROJECT_DIR/podman-pod.yaml" > "$PROJECT_DIR/podman-pod-resolved.yaml"
    
    # Start the pod
    podman kube play "$PROJECT_DIR/podman-pod-resolved.yaml"
    
    log_info "Pod started successfully!"
    log_info "Services will be available at:"
    echo "  - Traefik Dashboard: http://localhost:8090"
    echo "  - n8n: http://localhost:5678"
    echo "  - Open WebUI: http://localhost:3000"
    echo "  - Flowise: http://localhost:3001"
    echo "  - Langfuse: http://localhost:3002"
    echo "  - Ollama: http://localhost:11434"
    echo "  - Qdrant: http://localhost:6333"
    echo "  - SearXNG: http://localhost:8080"
}

# Function to stop the pod
stop_pod() {
    log_info "Stopping Local AI Stack pod..."
    podman kube down "$PROJECT_DIR/podman-pod-resolved.yaml" 2>/dev/null || true
    podman pod rm local-ai-stack 2>/dev/null || true
    log_info "Pod stopped successfully!"
}

# Function to show pod status
status_pod() {
    log_info "Pod status:"
    podman pod ps --filter name=local-ai-stack
    echo
    log_info "Container status:"
    podman ps --filter pod=local-ai-stack
}

# Function to show logs
logs_pod() {
    if [ -n "$1" ]; then
        log_info "Showing logs for container: $1"
        podman logs -f "$1"
    else
        log_info "Available containers:"
        podman ps --filter pod=local-ai-stack --format "{{.Names}}"
        echo
        log_info "Usage: $0 logs <container-name>"
    fi
}

# Function to pull Ollama models
setup_ollama() {
    log_info "Setting up Ollama models..."
    
    # Wait for Ollama to be ready
    sleep 10
    
    # Pull required models
    podman exec -it local-ai-stack-ollama ollama pull qwen2.5:7b-instruct-q4_K_M
    podman exec -it local-ai-stack-ollama ollama pull nomic-embed-text
    
    log_info "Ollama models installed successfully!"
}

# Main script logic
case "$1" in
    "setup")
        create_directories
        check_env_file
        log_info "Setup completed. Run '$0 start' to start the pod."
        ;;
    "start")
        create_directories
        check_env_file
        start_pod
        ;;
    "stop")
        stop_pod
        ;;
    "restart")
        stop_pod
        sleep 2
        start_pod
        ;;
    "status")
        status_pod
        ;;
    "logs")
        logs_pod "$2"
        ;;
    "ollama-setup")
        setup_ollama
        ;;
    *)
        echo "Usage: $0 {setup|start|stop|restart|status|logs [container]|ollama-setup}"
        echo
        echo "Commands:"
        echo "  setup       - Create directories and check environment"
        echo "  start       - Start the Local AI Stack pod"
        echo "  stop        - Stop the Local AI Stack pod"
        echo "  restart     - Restart the Local AI Stack pod"
        echo "  status      - Show pod and container status"
        echo "  logs        - Show logs for a specific container"
        echo "  ollama-setup - Pull required Ollama models"
        exit 1
        ;;
esac
