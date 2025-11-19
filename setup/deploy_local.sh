#!/usr/bin/env bash
set -euo pipefail

# Local Docker deployment script for AIVidFromPPT

IMAGE_NAME="aividfromppt"
IMAGE_TAG="latest"
CONTAINER_NAME="aividfromppt"
PORT="8201"
CONTEXT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DOCKERFILE="${CONTEXT_DIR}/.setup/Dockerfile"

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Options:
  -b, --build          Build Docker image before running
  -s, --stop           Stop and remove existing container
  -r, --restart        Stop, remove, build and run container
  -l, --logs           Show container logs
  -t, --tag TAG        Docker image tag (default: latest)
  -p, --port PORT      Container port (default: 8201)
  -e, --env-file FILE  Load environment variables from file
  -h, --help           Show this help message

Examples:
  $(basename "$0") --build              # Build and run
  $(basename "$0") --restart            # Full restart
  $(basename "$0") --logs               # View logs
  $(basename "$0") --stop               # Stop container
EOF
}

BUILD=false
STOP=false
RESTART=false
LOGS=false
ENV_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -b|--build)
      BUILD=true; shift;;
    -s|--stop)
      STOP=true; shift;;
    -r|--restart)
      RESTART=true; shift;;
    -l|--logs)
      LOGS=true; shift;;
    -t|--tag)
      IMAGE_TAG="$2"; shift 2;;
    -p|--port)
      PORT="$2"; shift 2;;
    -e|--env-file)
      ENV_FILE="$2"; shift 2;;
    -h|--help)
      usage; exit 0;;
    *)
      echo "[error] Unknown option: $1" >&2
      usage; exit 2;;
  esac
done

FULL_IMAGE="${IMAGE_NAME}:${IMAGE_TAG}"

# Check if Docker is installed
if ! command -v docker >/dev/null 2>&1; then
  echo "[error] Docker is not installed or not in PATH" >&2
  exit 127
fi

# Check if Dockerfile exists
if [[ ! -f "${DOCKERFILE}" ]]; then
  echo "[error] Dockerfile not found at: ${DOCKERFILE}" >&2
  exit 1
fi

# Stop and remove container
if [[ "${STOP}" == true ]] || [[ "${RESTART}" == true ]]; then
  echo "[info] Stopping container: ${CONTAINER_NAME}"
  docker stop "${CONTAINER_NAME}" 2>/dev/null || true
  echo "[info] Removing container: ${CONTAINER_NAME}"
  docker rm "${CONTAINER_NAME}" 2>/dev/null || true
fi

# Show logs
if [[ "${LOGS}" == true ]]; then
  if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    docker logs -f "${CONTAINER_NAME}"
  else
    echo "[error] Container ${CONTAINER_NAME} does not exist" >&2
    exit 1
  fi
  exit 0
fi

# Build image
if [[ "${BUILD}" == true ]] || [[ "${RESTART}" == true ]]; then
  echo "[info] Building Docker image: ${FULL_IMAGE}"
  echo "[info] Build context: ${CONTEXT_DIR}"
  echo "[info] Dockerfile: ${DOCKERFILE}"
  
  docker build \
    -f "${DOCKERFILE}" \
    -t "${FULL_IMAGE}" \
    --progress=plain \
    "${CONTEXT_DIR}"
  
  echo "[success] Image built: ${FULL_IMAGE}"
fi

# Check if image exists
if ! docker images --format '{{.Repository}}:{{.Tag}}' | grep -q "^${FULL_IMAGE}$"; then
  echo "[warn] Image ${FULL_IMAGE} not found. Building..."
  docker build \
    -f "${DOCKERFILE}" \
    -t "${FULL_IMAGE}" \
    --progress=plain \
    "${CONTEXT_DIR}"
fi

# Prepare environment variables
ENV_ARGS=()

# Load environment variables from file if provided
if [[ -n "${ENV_FILE}" ]]; then
  if [[ -f "${ENV_FILE}" ]]; then
    echo "[info] Loading environment variables from: ${ENV_FILE}"
    # Use Docker's --env-file option
    ENV_ARGS+=(--env-file "${ENV_FILE}")
  else
    echo "[warn] Environment file not found: ${ENV_FILE}"
  fi
fi

# Check for OPENAI_API_KEY in environment
if [[ -z "${OPENAI_API_KEY:-}" ]] && [[ -z "${ENV_FILE}" ]]; then
  echo "[warn] OPENAI_API_KEY not set in environment"
  echo "[hint] Set it with: export OPENAI_API_KEY='your-key-here'"
  echo "[hint] Or use: $(basename "$0") -e .env"
elif [[ -n "${OPENAI_API_KEY:-}" ]]; then
  ENV_ARGS+=(-e "OPENAI_API_KEY=${OPENAI_API_KEY}")
fi

# Create uploads directory if it doesn't exist
UPLOADS_DIR="${CONTEXT_DIR}/server/uploads"
mkdir -p "${UPLOADS_DIR}"

# Run container
echo "[info] Starting container: ${CONTAINER_NAME}"
echo "[info] Image: ${FULL_IMAGE}"
echo "[info] Port: ${PORT}"
echo "[info] Uploads directory: ${UPLOADS_DIR}"

docker run -d \
  --name "${CONTAINER_NAME}" \
  -p "${PORT}:8201" \
  -v "${UPLOADS_DIR}:/app/uploads" \
  "${ENV_ARGS[@]}" \
  "${FULL_IMAGE}"

# Wait a moment for container to start
sleep 2

# Check if container is running
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "[success] Container started successfully!"
  echo "[info] Container name: ${CONTAINER_NAME}"
  echo "[info] Access the API at: http://localhost:${PORT}"
  echo "[info] API documentation: http://localhost:${PORT}/docs"
  echo ""
  echo "[info] Useful commands:"
  echo "  View logs:    docker logs -f ${CONTAINER_NAME}"
  echo "  Stop:        docker stop ${CONTAINER_NAME}"
  echo "  Remove:       docker rm ${CONTAINER_NAME}"
  echo "  Shell:        docker exec -it ${CONTAINER_NAME} /bin/bash"
else
  echo "[error] Container failed to start" >&2
  echo "[info] Checking logs..."
  docker logs "${CONTAINER_NAME}" 2>&1 | tail -20
  exit 1
fi

