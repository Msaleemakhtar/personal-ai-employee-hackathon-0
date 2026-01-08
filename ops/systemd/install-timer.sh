#!/usr/bin/env bash
# Install systemd timer for AI Employee Queue Processor
# This replaces cron to handle suspend/resume properly

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing AI Employee systemd timer..."

# Copy service and timer files to systemd user directory
mkdir -p ~/.config/systemd/user
cp "$SCRIPT_DIR/ai-employee-queue.service" ~/.config/systemd/user/
cp "$SCRIPT_DIR/ai-employee-queue.timer" ~/.config/systemd/user/

# Reload systemd daemon
systemctl --user daemon-reload

# Enable and start the timer
systemctl --user enable ai-employee-queue.timer
systemctl --user start ai-employee-queue.timer

# Enable lingering (allows user services to run without being logged in)
sudo loginctl enable-linger "$USER"

echo ""
echo "Timer installed and started!"
echo ""
echo "To check status:  systemctl --user status ai-employee-queue.timer"
echo "To see next run:  systemctl --user list-timers ai-employee-queue.timer"
echo "To view logs:     journalctl --user -u ai-employee-queue.service -f"
echo ""
echo "IMPORTANT: Remove the old cron job with: crontab -e"
echo "           Delete the line with process_queue.sh"
