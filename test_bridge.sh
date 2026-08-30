#!/usr/bin/env bash

echo "1. Checking Bridge Health..."
curl -s http://127.0.0.1/health
echo -e "\n"

echo "2. Listing Models..."
curl -s http://127.0.0.1/v1/models
echo -e "\n"

echo "3. Testing Chat Completion..."
curl -s -X POST http://127.0.0.1/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "rhel-lightspeed",
    "messages": [
      {"role": "user", "content": "How to check active network ports in Linux?"}
    ]
  }'
echo -e "\n"
