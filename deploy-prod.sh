#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
APP_NAME="geosocial_api_prod"
HEALTH_CHECK_URL="http://localhost:8000/health"
MAX_WAIT_TIME=120

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not available"
        exit 1
    fi
    
    if [ ! -f ".env.prod" ]; then
        log_warn ".env.prod file not found. Creating from example..."
        cp env.example .env.prod
        log_warn "Please update .env.prod file with production values before deployment"
        exit 1
    fi
}

create_directories() {
    log_info "Creating required directories..."
    mkdir -p ./logs
    mkdir -p ./data/postgres
    mkdir -p ./data/redis
    chmod 755 ./logs ./data/postgres ./data/redis
}

backup_current() {
    if docker ps | grep -q $APP_NAME; then
        log_info "Backing up current deployment..."
        docker compose -f $COMPOSE_FILE logs > "./logs/deployment-backup-$(date +%Y%m%d-%H%M%S).log"
    fi
}

deploy() {
    log_info "Starting production deployment..."
    
    # Build and start services
    docker compose -f $COMPOSE_FILE down --remove-orphans
    docker compose -f $COMPOSE_FILE build --no-cache
    docker compose -f $COMPOSE_FILE up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 10
    
    # Health check
    local wait_time=0
    while [ $wait_time -lt $MAX_WAIT_TIME ]; do
        if curl -f $HEALTH_CHECK_URL > /dev/null 2>&1; then
            log_info "Application is healthy and ready!"
            return 0
        fi
        
        echo -n "."
        sleep 5
        wait_time=$((wait_time + 5))
    done
    
    log_error "Health check failed. Deployment may have issues."
    return 1
}

show_status() {
    log_info "Deployment status:"
    docker compose -f $COMPOSE_FILE ps
    
    log_info "Resource usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
    
    log_info "Recent logs (last 20 lines):"
    docker compose -f $COMPOSE_FILE logs --tail=20
}

rollback() {
    log_warn "Rolling back deployment..."
    docker compose -f $COMPOSE_FILE down
    # Here you could implement more sophisticated rollback logic
    log_info "Rollback completed. Check previous backups if needed."
}

# Main execution
main() {
    case "${1:-deploy}" in
        "deploy")
            check_dependencies
            create_directories
            backup_current
            if deploy; then
                show_status
                log_info "Production deployment completed successfully!"
            else
                log_error "Deployment failed!"
                exit 1
            fi
            ;;
        "status")
            show_status
            ;;
        "rollback")
            rollback
            ;;
        "logs")
            docker compose -f $COMPOSE_FILE logs -f
            ;;
        "stop")
            log_info "Stopping production deployment..."
            docker compose -f $COMPOSE_FILE down
            ;;
        *)
            echo "Usage: $0 {deploy|status|rollback|logs|stop}"
            echo "  deploy   - Deploy production environment (default)"
            echo "  status   - Show current status and resource usage"
            echo "  rollback - Rollback current deployment"
            echo "  logs     - Follow application logs"
            echo "  stop     - Stop production deployment"
            exit 1
            ;;
    esac
}

main "$@" 