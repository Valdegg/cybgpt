#!/bin/bash

# Replace with your actual API key
API_KEY="2XkjhABSzPbdMKqGyIhDxp8HadI_MQbGgUNMhGmzb3yLcXd"

# Get the list of tunnel session IDs
SESSION_IDS=$(curl -s -X GET \
-H "Authorization: Bearer $API_KEY" \
-H "Ngrok-Version: 2" \
https://api.ngrok.com/tunnel_sessions | jq -r '.tunnel_sessions[].id')

# Check if we got any session IDs
if [ -z "$SESSION_IDS" ]; then
    echo "No active ngrok sessions found."
    exit 0
fi

# Stop each tunnel session
for SESSION_ID in $SESSION_IDS; do
    echo "Stopping tunnel session $SESSION_ID"
    curl -s -X POST \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -H "Ngrok-Version: 2" \
    -d '{}' \
    "https://api.ngrok.com/tunnel_sessions/$SESSION_ID/stop"
    
    if [ $? -ne 0 ]; then
        echo "Failed to stop tunnel session $SESSION_ID"
    else
        echo "Tunnel session $SESSION_ID stopped successfully"
    fi
done
