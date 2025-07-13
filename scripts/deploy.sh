#!/bin/bash

# Heckx AI Video Generator Deployment Script
# Usage: ./scripts/deploy.sh [environment] [options]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="production"
SKIP_TESTS=false
SKIP_BACKUP=false
FORCE_DEPLOY=false
ROLLBACK=false
HEALTH_CHECK_TIMEOUT=300

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

usage() {
    cat << EOF
Heckx AI Video Generator Deployment Script

Usage: $0 [environment] [options]

Environments:
    development     Deploy to development environment
    staging         Deploy to staging environment
    production      Deploy to production environment (default)

Options:
    --skip-tests        Skip running tests before deployment
    --skip-backup       Skip database backup before deployment
    --force             Force deployment without confirmation
    --rollback          Rollback to previous deployment
    --help              Show this help message

Examples:
    $0 production                           # Deploy to production with all checks
    $0 staging --skip-tests                 # Deploy to staging without tests
    $0 production --force --skip-backup    # Force deploy without backup
    $0 production --rollback               # Rollback production deployment

EOF
}

check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker is not running"
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if environment file exists
    if [[ ! -f "$PROJECT_DIR/.env.$ENVIRONMENT" ]]; then
        error "Environment file .env.$ENVIRONMENT not found"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

run_tests() {
    if [[ "$SKIP_TESTS" == "true" ]]; then
        warning "Skipping tests"
        return 0
    fi
    
    log "Running tests..."
    cd "$PROJECT_DIR"
    
    # Run test suite
    if ! python -m pytest tests/ -v --tb=short; then
        error "Tests failed"
        exit 1
    fi
    
    success "All tests passed"
}

create_backup() {
    if [[ "$SKIP_BACKUP" == "true" ]]; then
        warning "Skipping backup"
        return 0
    fi
    
    log "Creating backup..."
    
    # Create backup directory with timestamp
    BACKUP_DIR="$PROJECT_DIR/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup database if in production
    if [[ "$ENVIRONMENT" == "production" ]]; then
        log "Backing up production database..."
        docker-compose -f docker-compose.prod.yml exec -T postgres \
            pg_dump -U postgres heckx_video_prod > "$BACKUP_DIR/database.sql"
        
        # Backup application data
        docker run --rm -v heckx_data:/data -v "$BACKUP_DIR":/backup \
            ubuntu tar czf /backup/app_data.tar.gz -C /data .
    fi
    
    # Backup current deployment configuration
    cp docker-compose*.yml "$BACKUP_DIR/" 2>/dev/null || true
    cp .env.* "$BACKUP_DIR/" 2>/dev/null || true
    
    success "Backup created at $BACKUP_DIR"
    echo "$BACKUP_DIR" > "$PROJECT_DIR/.last_backup"
}

build_and_push_image() {
    log "Building Docker image..."
    cd "$PROJECT_DIR"
    
    # Build image with timestamp tag
    IMAGE_TAG="heckx-video-generator:$(date +%Y%m%d_%H%M%S)"
    LATEST_TAG="heckx-video-generator:latest"
    
    if ! docker build -t "$IMAGE_TAG" -t "$LATEST_TAG" .; then
        error "Docker build failed"
        exit 1
    fi
    
    # If using a registry, push the image
    if [[ -n "${DOCKER_REGISTRY:-}" ]]; then
        log "Pushing image to registry..."
        REGISTRY_IMAGE="$DOCKER_REGISTRY/$IMAGE_TAG"
        docker tag "$IMAGE_TAG" "$REGISTRY_IMAGE"
        docker push "$REGISTRY_IMAGE"
        
        # Update docker-compose to use registry image
        sed -i.bak "s|image: heckx-video-generator:latest|image: $REGISTRY_IMAGE|g" \
            "docker-compose.$ENVIRONMENT.yml"
    fi
    
    success "Image built successfully: $IMAGE_TAG"
}

deploy_application() {
    log "Deploying application to $ENVIRONMENT..."
    cd "$PROJECT_DIR"
    
    # Copy environment file
    cp ".env.$ENVIRONMENT" .env
    
    # Choose appropriate docker-compose file
    COMPOSE_FILE="docker-compose.yml"
    if [[ -f "docker-compose.$ENVIRONMENT.yml" ]]; then
        COMPOSE_FILE="docker-compose.$ENVIRONMENT.yml"
    fi
    
    # Pull latest images
    docker-compose -f "$COMPOSE_FILE" pull
    
    # Start services with rolling update
    log "Starting services..."
    docker-compose -f "$COMPOSE_FILE" up -d --remove-orphans
    
    success "Application deployed"
}

wait_for_health_check() {
    log "Waiting for health check..."
    
    # Determine health check URL based on environment
    case "$ENVIRONMENT" in
        "development")
            HEALTH_URL="http://localhost:5002/api/health"
            ;;
        "staging")
            HEALTH_URL="https://staging.heckx.ai/api/health"
            ;;
        "production")
            HEALTH_URL="https://heckx.ai/api/health"
            ;;
        *)
            HEALTH_URL="http://localhost:5002/api/health"
            ;;
    esac
    
    # Wait for health check to pass
    ELAPSED=0
    while [[ $ELAPSED -lt $HEALTH_CHECK_TIMEOUT ]]; do
        if curl -f -s "$HEALTH_URL" > /dev/null 2>&1; then
            success "Health check passed"
            return 0
        fi
        
        echo -n "."
        sleep 5
        ELAPSED=$((ELAPSED + 5))
    done
    
    error "Health check failed after ${HEALTH_CHECK_TIMEOUT}s"
    return 1
}

rollback_deployment() {
    log "Rolling back deployment..."
    
    if [[ ! -f "$PROJECT_DIR/.last_backup" ]]; then
        error "No backup information found"
        exit 1
    fi
    
    BACKUP_DIR=$(cat "$PROJECT_DIR/.last_backup")
    
    if [[ ! -d "$BACKUP_DIR" ]]; then
        error "Backup directory not found: $BACKUP_DIR"
        exit 1
    fi
    
    # Stop current services
    docker-compose down
    
    # Restore configuration files
    cp "$BACKUP_DIR"/docker-compose*.yml "$PROJECT_DIR/" 2>/dev/null || true
    cp "$BACKUP_DIR"/.env.* "$PROJECT_DIR/" 2>/dev/null || true
    
    # Restore database if available
    if [[ -f "$BACKUP_DIR/database.sql" ]]; then
        log "Restoring database..."
        docker-compose -f docker-compose.prod.yml up -d postgres
        sleep 10
        docker-compose -f docker-compose.prod.yml exec -T postgres \
            psql -U postgres -d heckx_video_prod < "$BACKUP_DIR/database.sql"
    fi
    
    # Restore application data
    if [[ -f "$BACKUP_DIR/app_data.tar.gz" ]]; then
        log "Restoring application data..."
        docker run --rm -v heckx_data:/data -v "$BACKUP_DIR":/backup \
            ubuntu tar xzf /backup/app_data.tar.gz -C /data
    fi
    
    # Start services
    docker-compose up -d
    
    success "Rollback completed"
}

cleanup_old_images() {
    log "Cleaning up old Docker images..."
    
    # Remove images older than 7 days
    docker image prune -a -f --filter "until=168h" || true
    
    # Clean up build cache
    docker builder prune -f || true
    
    success "Cleanup completed"
}

send_notification() {
    local status=$1
    local message=$2
    
    # Send Slack notification if webhook is configured
    if [[ -n "${SLACK_WEBHOOK:-}" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$message\"}" \
            "$SLACK_WEBHOOK" 2>/dev/null || true
    fi
    
    # Send email notification if configured
    if [[ -n "${NOTIFICATION_EMAIL:-}" ]]; then
        echo "$message" | mail -s "Heckx Deployment $status" "$NOTIFICATION_EMAIL" 2>/dev/null || true
    fi
}

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            development|staging|production)
                ENVIRONMENT="$1"
                shift
                ;;
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --skip-backup)
                SKIP_BACKUP=true
                shift
                ;;
            --force)
                FORCE_DEPLOY=true
                shift
                ;;
            --rollback)
                ROLLBACK=true
                shift
                ;;
            --help)
                usage
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
    
    # Print deployment banner
    cat << EOF

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎬 Heckx AI Video Generator Deployment
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Environment: $ENVIRONMENT
Skip Tests: $SKIP_TESTS
Skip Backup: $SKIP_BACKUP
Force Deploy: $FORCE_DEPLOY
Rollback: $ROLLBACK

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOF
    
    # Handle rollback
    if [[ "$ROLLBACK" == "true" ]]; then
        if [[ "$FORCE_DEPLOY" != "true" ]]; then
            read -p "Are you sure you want to rollback? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log "Rollback cancelled"
                exit 0
            fi
        fi
        
        rollback_deployment
        wait_for_health_check
        send_notification "SUCCESS" "🔄 Heckx Video Generator rollback completed for $ENVIRONMENT"
        exit 0
    fi
    
    # Confirmation for production
    if [[ "$ENVIRONMENT" == "production" && "$FORCE_DEPLOY" != "true" ]]; then
        warning "You are about to deploy to PRODUCTION!"
        read -p "Are you sure you want to continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "Deployment cancelled"
            exit 0
        fi
    fi
    
    # Start deployment process
    START_TIME=$(date +%s)
    
    # Deployment steps
    check_prerequisites
    run_tests
    create_backup
    build_and_push_image
    deploy_application
    
    # Wait for application to be ready
    if wait_for_health_check; then
        cleanup_old_images
        
        END_TIME=$(date +%s)
        DURATION=$((END_TIME - START_TIME))
        
        success "🎉 Deployment completed successfully in ${DURATION}s"
        send_notification "SUCCESS" "🚀 Heckx Video Generator deployed successfully to $ENVIRONMENT in ${DURATION}s"
    else
        error "Deployment failed - health check did not pass"
        send_notification "FAILED" "❌ Heckx Video Generator deployment failed in $ENVIRONMENT"
        
        # Auto-rollback on production failure
        if [[ "$ENVIRONMENT" == "production" ]]; then
            warning "Auto-rolling back production deployment..."
            rollback_deployment
        fi
        
        exit 1
    fi
}

# Run main function
main "$@"