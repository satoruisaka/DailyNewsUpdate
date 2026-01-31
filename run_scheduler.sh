#!/bin/bash

# Daily News Agent Scheduler Runner

# Set working directory
cd /home/sator/project/NewsAgent

# Activate virtual environment
source ./.venv/bin/activate

# Log file path
LOG_DIR="/home/sator/project/NewsAgent/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/cron_$(date +\%Y-\%m-\%d).log"

# Timestamp
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Log execution time
echo "=====================================" >> "$LOG_FILE"
echo "News Agent execution started at $TIMESTAMP" >> "$LOG_FILE"

# Set Python path
export PYTHONPATH=/home/sator/project/NewsAgent:$PYTHONPATH

# Run the scheduler
python /home/sator/project/NewsAgent/scheduler.py >> "$LOG_FILE" 2>&1

# Log completion
echo "News Agent execution completed at $TIMESTAMP" >> "$LOG_FILE"
echo "=====================================" >> "$LOG_FILE"