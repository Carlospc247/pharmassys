#!/bin/bash
set -e

# Replace {YOUR_GIT_REOPO_URL} with your actual Git repository URL
#GIT_REPO_URL="https://github.com/Carlospc247/vistogest-pro.git"

# If using Private Repo
GIT_REPO_URL="https://Carlospc247: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@github.com/Carlospc247/vistogest-pro.git"

# Replace {YOUR_PROJECT_MAIN_DIR_NAME} with your actual project directory name
PROJECT_MAIN_DIR_NAME="vistogest-pro"

# Clone repository
git clone "$GIT_REPO_URL" "/var/www/$PROJECT_MAIN_DIR_NAME"

cd "/var/www/$PROJECT_MAIN_DIR_NAME"

# Make all .sh files executable
chmod +x scripts/*.sh

# Execute scripts for OS dependencies, Python dependencies, Gunicorn, Nginx, and starting the application
./scripts/instance_os_dependencies.sh
./scripts/python_dependencies.sh
./scripts/gunicorn.sh
./scripts/nginx.sh
./scripts/start_app.sh
