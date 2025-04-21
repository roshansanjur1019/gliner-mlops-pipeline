#!/bin/bash
set -e

# Script to deploy GLiNER MLOps pipeline to Kubernetes
# Usage: ./deploy.sh <environment> [options]
#
# Environments:
#   dev          Development environment
#   staging      Staging environment
#   prod         Production environment
#
# Options:
#   --dry-run    Perform a dry run without making changes
#   --verbose    Show verbose output
#   --force      Skip confirmation prompts

# Configuration
NAMESPACE_PREFIX="mlops"
KUBE_CONFIG="${KUBE_CONFIG:-$HOME/.kube/config}"
IMAGE_REPO="${ECR_REPOSITORY_URI:-gliner-mlops}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

# Parse arguments
if [ $# -lt 1 ]; then
  echo "Error: Missing environment parameter"
  echo "Usage: ./deploy.sh <environment> [options]"
  exit 1
fi

ENVIRONMENT=$1
shift

case $ENVIRONMENT in
  dev|development)
    ENVIRONMENT="dev"
    NAMESPACE="${NAMESPACE_PREFIX}-dev"
    CONFIG_ENV="development"
    REPLICAS=1
    ;;
  staging)
    ENVIRONMENT="staging"
    NAMESPACE="${NAMESPACE_PREFIX}-staging"
    CONFIG_ENV="staging"
    REPLICAS=2
    ;;
  prod|production)
    ENVIRONMENT="prod"
    NAMESPACE="${NAMESPACE_PREFIX}-prod"
    CONFIG_ENV="production"
    REPLICAS=3
    ;;
  *)
    echo "Error: Invalid environment '$ENVIRONMENT'"
    echo "Valid environments: dev, staging, prod"
    exit 1
    ;;
esac

# Parse options
DRY_RUN=0
VERBOSE=0
FORCE=0

for arg in "$@"; do
  case $arg in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --verbose)
      VERBOSE=1
      shift
      ;;
    --force)
      FORCE=1
      shift
      ;;
  esac
done

# Set up logging
log() {
  echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')] $1"
}

# Verbose logging
log_verbose() {
  if [ $VERBOSE -eq 1 ]; then
    log "$1"
  fi
}

# Execute Kubernetes command
kubectl_cmd() {
  cmd="kubectl --kubeconfig=$KUBE_CONFIG $1"
  
  if [ $DRY_RUN -eq 1 ]; then
    cmd="$cmd --dry-run=client -o yaml"
  fi
  
  if [ $VERBOSE -eq 1 ]; then
    log "Executing: $cmd"
  fi
  
  eval $cmd
}

# Main deployment function
main() {
  log "Starting deployment to $ENVIRONMENT environment..."
  
  # Confirm deployment for production
  if [ "$ENVIRONMENT" == "prod" ] && [ $FORCE -eq 0 ] && [ $DRY_RUN -eq 0 ]; then
    read -p "Are you sure you want to deploy to PRODUCTION? (y/N) " confirm
    if [[ $confirm != [yY] && $confirm != [yY][eE][sS] ]]; then
      log "Deployment to production aborted."
      exit 0
    fi
  fi
  
  # Create namespace if it doesn't exist
  log "Ensuring namespace $NAMESPACE exists..."
  kubectl_cmd "create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -"
  
  # Update Kubernetes manifests with environment-specific values
  log "Preparing Kubernetes manifests for $ENVIRONMENT environment..."
  
  # Create a temporary directory for modified manifests
  TMP_DIR=$(mktemp -d)
  trap "rm -rf $TMP_DIR" EXIT
  
  # Copy and update manifest files
  for file in k8s/*.yaml; do
    filename=$(basename $file)
    cp $file $TMP_DIR/$filename
    
    # Replace placeholders in manifests
    sed -i "s/\${ENVIRONMENT}/$ENVIRONMENT/g" $TMP_DIR/$filename
    sed -i "s/\${NAMESPACE}/$NAMESPACE/g" $TMP_DIR/$filename
    sed -i "s/\${IMAGE_REPO}/$IMAGE_REPO/g" $TMP_DIR/$filename
    sed -i "s/\${IMAGE_TAG}/$IMAGE_TAG/g" $TMP_DIR/$filename
    sed -i "s/replicas: [0-9]\+/replicas: $REPLICAS/g" $TMP_DIR/$filename
    
    log_verbose "Updated $filename for $ENVIRONMENT environment"
  done
  
  # Apply ConfigMap first
  if [ -f $TMP_DIR/configmap.yaml ]; then
    log "Applying ConfigMap..."
    kubectl_cmd "apply -f $TMP_DIR/configmap.yaml -n $NAMESPACE"
  fi
  
  # Apply Secrets
  if [ -f $TMP_DIR/secrets.yaml ]; then
    log "Applying Secrets..."
    kubectl_cmd "apply -f $TMP_DIR/secrets.yaml -n $NAMESPACE"
  fi
  
  # Apply Service accounts, roles, and bindings
  log "Applying RBAC resources..."
  for file in $TMP_DIR/*rbac*.yaml; do
    if [ -f "$file" ]; then
      kubectl_cmd "apply -f $file -n $NAMESPACE"
    fi
  done
  
  # Apply CRDs and other infrastructure
  log "Applying infrastructure resources..."
  kubectl_cmd "apply -f $TMP_DIR/service.yaml -n $NAMESPACE"
  
  # Apply Deployment last
  log "Applying Deployment..."
  kubectl_cmd "apply -f $TMP_DIR/deployment.yaml -n $NAMESPACE"
  
  # Apply HPA
  if [ -f $TMP_DIR/hpa.yaml ]; then
    log "Applying HorizontalPodAutoscaler..."
    kubectl_cmd "apply -f $TMP_DIR/hpa.yaml -n $NAMESPACE"
  fi
  
  # Apply Ingress
  if [ -f $TMP_DIR/ingress.yaml ]; then
    log "Applying Ingress..."
    kubectl_cmd "apply -f $TMP_DIR/ingress.yaml -n $NAMESPACE"
  fi
  
  # Wait for deployment to complete
  if [ $DRY_RUN -eq 0 ]; then
    log "Waiting for deployment to complete..."
    kubectl --kubeconfig=$KUBE_CONFIG rollout status deployment/gliner-api -n $NAMESPACE --timeout=300s
  fi
  
  log "Deployment to $ENVIRONMENT completed successfully!"
}

# Execute main function
main