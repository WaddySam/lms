#!/bin/bash
echo "TEST SCRIPT RUNNING"
echo "User: $(whoami)"
echo "Date: $(date)"
echo "PORT: ${PORT:-8000}"

# Keep container alive for testing
echo "Sleeping for 60 seconds to keep container alive..."
sleep 60
echo "Sleep complete, exiting"
