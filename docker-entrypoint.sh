#!/bin/bash
# Docker entrypoint script for Network Security MLOps
# Handles different execution modes: api, train, test

set -e

MODE=${1:-api}

echo "=========================================="
echo "Network Security MLOps Container"
echo "Mode: $MODE"
echo "=========================================="

case "$MODE" in
    api)
        echo "Starting FastAPI prediction service..."
        exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WORKERS:-4}
        ;;
    
    train)
        echo "Starting training pipeline..."
        exec python main.py
        ;;
    
    test)
        echo "Running tests..."
        if [ -f "tests/run_tests.py" ]; then
            exec python tests/run_tests.py
        else
            echo "No test file found. Running pytest..."
            exec pytest tests/ -v
        fi
        ;;
    
    retrain)
        echo "Starting retraining pipeline..."
        exec python scheduled_retrain.py "$@"
        ;;
    
    bash|sh)
        echo "Starting interactive shell..."
        exec /bin/bash
        ;;
    
    *)
        echo "Unknown mode: $MODE"
        echo "Available modes: api, train, test, retrain, bash"
        exit 1
        ;;
esac
