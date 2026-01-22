#!/bin/bash

# OCR System Deployment Script for VPS
# This script deploys the OCR system to your VPS using Docker

set -e  # Exit on error

echo "🚀 Starting OCR System Deployment"
echo "=================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Get server IP for API URL
echo -e "${YELLOW}Enter your server IP address (for API connection):${NC}"
read SERVER_IP

# Update docker-compose.yml with server IP
sed -i "s/YOUR_SERVER_IP/$SERVER_IP/g" docker-compose.yml

echo -e "${GREEN}✓${NC} Updated API URL to http://$SERVER_IP:8001"

# Stop existing containers if any
echo -e "\n${YELLOW}Stopping existing OCR containers...${NC}"
docker-compose down || true

# Build images
echo -e "\n${YELLOW}Building Docker images (this may take 5-10 minutes)...${NC}"
docker-compose build --no-cache

# Start containers
echo -e "\n${YELLOW}Starting containers...${NC}"
docker-compose up -d

# Wait for services to be healthy
echo -e "\n${YELLOW}Waiting for services to start...${NC}"
sleep 10

# Check container status
echo -e "\n${GREEN}Container Status:${NC}"
docker-compose ps

# Display logs
echo -e "\n${GREEN}Recent logs:${NC}"
docker-compose logs --tail=20

echo -e "\n${GREEN}=================================="
echo -e "✅ Deployment Complete!"
echo -e "=================================="
echo -e "${GREEN}OCR Backend:${NC}  http://$SERVER_IP:8001"
echo -e "${GREEN}OCR Frontend:${NC} http://$SERVER_IP:3001"
echo -e "\n${YELLOW}Useful commands:${NC}"
echo -e "  View logs:    docker-compose logs -f"
echo -e "  Stop:         docker-compose down"
echo -e "  Restart:      docker-compose restart"
echo -e "  Update:       git pull && docker-compose up -d --build"
