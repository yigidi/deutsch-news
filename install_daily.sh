#!/usr/bin/env bash
# Install daily runner for macOS (launchd)

set -e

PROJECT_DIR="/Users/fatihaktemur/Documents/Default Project/deutsch_news"
PLIST_SRC="$PROJECT_DIR/com.deutschnews.daily.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.deutschnews.daily.plist"
LOG_DIR="$PROJECT_DIR/logs"

echo "📅 Installing daily runner (runs every day at 18:00)..."

# Create logs directory
mkdir -p "$LOG_DIR"

# Update plist with correct paths
sed "s|/Users/fatihaktemur/Documents/Default Project/deutsch_news|$PROJECT_DIR|g" "$PLIST_SRC" > "$PLIST_DST"

# Load the launch agent
launchctl unload "$PLIST_DST" 2>/dev/null || true
launchctl load "$PLIST_DST"

echo "✅ Daily runner installed!"
echo ""
echo "The site will now be regenerated every day at 18:00."
echo ""
echo "To check status: launchctl list | grep deutschnews"
echo "To view logs: tail -f $LOG_DIR/daily.log"
echo "To uninstall: launchctl unload $PLIST_DST && rm $PLIST_DST"