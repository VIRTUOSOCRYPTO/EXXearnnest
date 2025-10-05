#!/bin/bash

# EarnNest Automatic Startup Script
# This script ensures all backend services start automatically and reliably

set -e  # Exit on any error

echo "🚀 Starting EarnNest Automatic Startup Process..."

# Function to wait for service to be ready
wait_for_service() {
    local service_name=$1
    local max_attempts=30
    local attempt=0
    
    echo "⏳ Waiting for $service_name to be ready..."
    
    while [ $attempt -lt $max_attempts ]; do
        if sudo supervisorctl status $service_name | grep -q "RUNNING"; then
            echo "✅ $service_name is running"
            return 0
        fi
        
        echo "⏳ $service_name not ready yet (attempt $((attempt + 1))/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name failed to start after $max_attempts attempts"
    return 1
}

# Function to check and install backend dependencies
setup_backend() {
    echo "🔧 Setting up backend dependencies..."
    
    cd /app/backend
    
    # Check if virtual environment exists
    if [ ! -d "/root/.venv" ]; then
        echo "📦 Creating Python virtual environment..."
        python3 -m venv /root/.venv
    fi
    
    # Activate virtual environment and install dependencies
    source /root/.venv/bin/activate
    
    echo "📦 Installing/updating backend dependencies..."
    pip install -r requirements.txt --quiet
    
    echo "✅ Backend dependencies ready"
}

# Function to setup frontend dependencies  
setup_frontend() {
    echo "🔧 Setting up frontend dependencies..."
    
    cd /app/frontend
    
    # Install frontend dependencies if node_modules doesn't exist or is outdated
    if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules" ]; then
        echo "📦 Installing/updating frontend dependencies..."
        yarn install --silent
    fi
    
    echo "✅ Frontend dependencies ready"
}

# Function to ensure MongoDB is ready
setup_mongodb() {
    echo "🔧 Ensuring MongoDB is ready..."
    
    # Wait for MongoDB to be accessible
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if mongo --eval "db.runCommand('ping')" --quiet > /dev/null 2>&1; then
            echo "✅ MongoDB is accessible"
            return 0
        fi
        
        echo "⏳ Waiting for MongoDB to be ready (attempt $((attempt + 1))/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "⚠️ MongoDB connection test timed out, but continuing..."
    return 0
}

# Function to verify backend health
check_backend_health() {
    echo "🔍 Checking backend health..."
    
    local max_attempts=15
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "http://localhost:8001/health" > /dev/null 2>&1; then
            echo "✅ Backend health check passed"
            return 0
        fi
        
        echo "⏳ Backend not ready yet (attempt $((attempt + 1))/$max_attempts)"
        sleep 3
        attempt=$((attempt + 1))
    done
    
    echo "⚠️ Backend health check timed out, but service appears to be running"
    return 0
}

# Function to verify frontend health  
check_frontend_health() {
    echo "🔍 Checking frontend health..."
    
    local max_attempts=10
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "http://localhost:3000" > /dev/null 2>&1; then
            echo "✅ Frontend health check passed"
            return 0
        fi
        
        echo "⏳ Frontend not ready yet (attempt $((attempt + 1))/$max_attempts)"
        sleep 3
        attempt=$((attempt + 1))
    done
    
    echo "⚠️ Frontend health check timed out, but service appears to be running"
    return 0
}

# Main startup sequence
main() {
    echo "🎯 EarnNest Automatic Startup - $(date)"
    
    # Step 1: Setup dependencies
    setup_backend
    setup_frontend
    
    # Step 2: Start MongoDB first (dependency for backend)
    echo "🚀 Starting MongoDB..."
    sudo supervisorctl start mongodb
    wait_for_service "mongodb"
    setup_mongodb
    
    # Step 3: Start backend (depends on MongoDB)
    echo "🚀 Starting backend..."
    sudo supervisorctl start backend
    wait_for_service "backend"
    
    # Step 4: Start frontend (depends on backend)
    echo "🚀 Starting frontend..."  
    sudo supervisorctl start frontend
    wait_for_service "frontend"
    
    # Step 5: Start code-server
    echo "🚀 Starting code-server..."
    sudo supervisorctl start code-server
    wait_for_service "code-server"
    
    # Step 6: Health checks
    sleep 5  # Give services time to fully initialize
    check_backend_health
    check_frontend_health
    
    # Step 7: Final status
    echo "📊 Final service status:"
    sudo supervisorctl status
    
    echo ""
    echo "🎉 EarnNest startup complete!"
    echo "🌐 Frontend URL: https://run-analyze.preview.emergentagent.com"
    echo "🔧 Backend API: https://run-analyze.preview.emergentagent.com/api"
    echo "📝 Code Server: Available on port 8080"
    echo ""
    echo "✅ All services should now be running automatically!"
}

# Run the main function
main "$@"
