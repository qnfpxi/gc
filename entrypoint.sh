#!/bin/bash
set -e

# entrypoint.sh - Entrypoint script for starting the Stock Analysis API service

echo "--- Starting Stock Analysis API Service ---"

# 1. Set Python path to ensure project modules can be found
# If your stock_analysis_api.py is in the project root and your command is executed from the project root,
# then usually no extra PYTHONPATH setting is needed, as Python automatically searches the current directory.
# But for robustness, or if the project structure is more complex, you can add:
# export PYTHONPATH=$PYTHONPATH:/app # Assuming your code is in /app directory within the container

# 2. Validate environment variables
echo "Validating environment variables..."
if [ -z "$STOCK_API_TUSHARE_TOKEN" ]; then
    echo "Error: STOCK_API_TUSHARE_TOKEN environment variable is not set! Please set it in .env file or Docker environment variables."
    exit 1
fi
if [ -z "$STOCK_API_REDIS_HOST" ]; then
    echo "Warning: STOCK_API_REDIS_HOST environment variable is not set, will use default value localhost."
fi
# Redis password is now optional, so no validation needed here for it
echo "Environment variable validation completed."

# 3. Execute cache preheating (optional, but recommended for production)
# This step runs the preheat_cache.py script to load common data into Redis in advance.
echo "Executing cache preheating (preheat_cache.py)..."
python /app/preheat_cache.py # Assuming preheat_cache.py is located in /app directory
if [ $? -ne 0 ]; then
    echo "Warning: Cache preheating failed, the service will continue to start, but the first request might be slower."
fi
echo "Cache preheating completed."

# 4. Start the main application (FastAPI with Uvicorn)
# Use uvicorn to start the FastAPI application
# --host 0.0.0.0 allows external access
# --port 8000 listens on port 8000
# --workers 2 can be adjusted based on CPU cores and memory, production environments usually set to (2 * CPU_CORES + 1)
# --log-level info sets the log level
echo "Starting FastAPI application..."
exec uvicorn stock_analysis_api:app --host 0.0.0.0 --port 8000 --workers 2 --log-level info

# Note: The `exec` command replaces the current shell process with the uvicorn process,
# so signals (like SIGTERM) can be directly passed to uvicorn for graceful shutdown.

