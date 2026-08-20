#!/usr/bin/env bash
# Upload a local PNG to LinkedIn via presigned upload URL
# Usage: ./upload_image_to_linkedin.sh <image.png> <upload_url>
set -euo pipefail

IMAGE="${1:?Usage: $0 <image.png> <upload_url>}"
UPLOAD_URL="${2:?Usage: $0 <image.png> <upload_url>}"

if [ ! -f "$IMAGE" ]; then
    echo "Error: File not found: $IMAGE"
    exit 1
fi

echo "Uploading $IMAGE to LinkedIn..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}"     -X PUT     -H "Content-Type: image/png"     --data-binary "@$IMAGE"     "$UPLOAD_URL")

if [ "$HTTP_CODE" = "201" ]; then
    echo "✅ Upload successful (HTTP 201)"
    exit 0
else
    echo "❌ Upload failed (HTTP $HTTP_CODE)"
    exit 1
fi
