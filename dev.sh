#!/bin/bash

# AI Research Platform Development Script
# Quick commands for common development tasks

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

show_help() {
    echo "🔬 AI Research Platform Development Helper"
    echo "=========================================="
    echo ""
    echo "Usage: ./dev.sh [command]"
    echo ""
    echo "Commands:"
    echo "  setup     - Run initial setup"
    echo "  run       - Start the development server"
    echo "  test      - Run tests"
    echo "  lint      - Run code linting"
    echo "  format    - Format code with black and isort"
    echo "  clean     - Clean up generated files"
    echo "  docker    - Build and run with Docker"
    echo "  help      - Show this help message"
    echo ""
}

setup_env() {
    echo "🔄 Setting up development environment..."
    ./setup.sh
}

run_server() {
    echo "🚀 Starting development server..."
    source .venv/bin/activate
    python app.py
}

run_tests() {
    echo "🧪 Running tests..."
    source .venv/bin/activate
    python -m pytest tests/ -v --cov=. --cov-report=term-missing
}

run_lint() {
    echo "🔍 Running linting..."
    source .venv/bin/activate
    echo "Running flake8..."
    flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || true
    echo "Running black check..."
    black --check . || true
    echo "Running isort check..."
    isort --check-only . || true
}

format_code() {
    echo "🎨 Formatting code..."
    source .venv/bin/activate
    echo "Running black..."
    black .
    echo "Running isort..."
    isort .
    echo "✅ Code formatted"
}

clean_up() {
    echo "🧹 Cleaning up..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "*.pyo" -delete 2>/dev/null || true
    find . -name "*.pyd" -delete 2>/dev/null || true
    find . -name ".coverage" -delete 2>/dev/null || true
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    echo "✅ Cleanup complete"
}

docker_run() {
    echo "🐳 Building and running with Docker..."
    docker-compose down || true
    docker-compose build
    docker-compose up
}

case "${1:-help}" in
    setup)
        setup_env
        ;;
    run)
        run_server
        ;;
    test)
        run_tests
        ;;
    lint)
        run_lint
        ;;
    format)
        format_code
        ;;
    clean)
        clean_up
        ;;
    docker)
        docker_run
        ;;
    help|*)
        show_help
        ;;
esac
