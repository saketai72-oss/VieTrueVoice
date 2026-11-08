#!/usr/bin/env bash
# =====================================================================
# ViTrueVoice Automated AWS EC2 Deployment Script
# Supports: Amazon Linux 2023 / Ubuntu 22.04 LTS (x86_64)
# Tech: Docker, Docker Compose, AWS ECR, NVIDIA Container Toolkit (GPU)
# =====================================================================

set -euo pipefail

# Configuration parameters
AWS_REGION="${AWS_REGION:-ap-southeast-1}"
ECR_REGISTRY="${ECR_REGISTRY:-123456789012.dkr.ecr.ap-southeast-1.amazonaws.com}"
IMAGE_NAME="${IMAGE_NAME:-vitruevoice:latest}"
APP_DIR="${APP_DIR:-/opt/vitruevoice}"

echo "====================================================================="
echo " Starting ViTrueVoice AWS EC2 Deployment"
echo " Region:    ${AWS_REGION}"
echo " Registry:  ${ECR_REGISTRY}"
echo " App Dir:   ${APP_DIR}"
echo "====================================================================="

# 1. Update OS and install prerequisites
if command -v dnf &> /dev/null; then
    echo "[1/6] Detected Amazon Linux / RHEL. Installing packages via dnf..."
    sudo dnf update -y
    sudo dnf install -y docker git curl
elif command -v apt-get &> /dev/null; then
    echo "[1/6] Detected Debian / Ubuntu. Installing packages via apt..."
    sudo apt-get update -y
    sudo apt-get install -y docker.io docker-compose-plugin git curl
fi

# 2. Start and enable Docker service
echo "[2/6] Enabling and starting Docker daemon..."
sudo systemctl enable --now docker
sudo usermod -aG docker "${USER}" || true

# 3. Detect NVIDIA GPU and install Container Toolkit if present
if lspci | grep -qi nvidia; then
    echo "[3/6] NVIDIA GPU detected. Configuring NVIDIA Container Toolkit..."
    if command -v dnf &> /dev/null; then
        curl -s -L https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo | sudo tee /etc/yum.repos.d/nvidia-container-toolkit.repo
        sudo dnf install -y nvidia-container-toolkit
    elif command -v apt-get &> /dev/null; then
        curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
        curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
            sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
            sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
        sudo apt-get update
        sudo apt-get install -y nvidia-container-toolkit
    fi
    sudo nvidia-ctk runtime configure --runtime=docker
    sudo systemctl restart docker
else
    echo "[3/6] No NVIDIA GPU detected. Running in optimized CPU mode."
fi

# 4. Prepare workspace
echo "[4/6] Setting up application directory..."
sudo mkdir -p "${APP_DIR}/out" "${APP_DIR}/benchmarks"
sudo chown -R "${USER}:${USER}" "${APP_DIR}"
cd "${APP_DIR}"

# 5. ECR Login and Image Pull
echo "[5/6] Authenticating with Amazon ECR..."
if command -v aws &> /dev/null; then
    aws ecr get-login-password --region "${AWS_REGION}" | docker login --username AWS --password-stdin "${ECR_REGISTRY}" || echo "Warning: ECR login skipped or failed (using local image if available)."
fi

# If repository cloned, use docker-compose
if [ -f "docker-compose.yml" ]; then
    echo "Starting services via docker-compose..."
    docker compose down || true
    docker compose up -d
else
    echo "Starting standalone Docker container..."
    docker stop vitruevoice-api 2>/dev/null || true
    docker rm vitruevoice-api 2>/dev/null || true
    docker run -d \
        --name vitruevoice-api \
        --restart unless-stopped \
        -p 8000:8000 \
        -v "${APP_DIR}/out:/app/out:ro" \
        -v "${APP_DIR}/benchmarks:/app/benchmarks" \
        "${ECR_REGISTRY}/${IMAGE_NAME}"
fi

# 6. Verify health endpoint
echo "[6/6] Verifying health status..."
sleep 5
for i in {1..10}; do
    if curl -s -f http://localhost:8000/health > /dev/null; then
        echo "SUCCESS: ViTrueVoice API is HEALTHY on port 8000!"
        curl -s http://localhost:8000/health | python3 -m json.tool || true
        exit 0
    fi
    echo "Waiting for service to become healthy... ($i/10)"
    sleep 3
done

echo "ERROR: Health check timed out after 30 seconds."
exit 1
