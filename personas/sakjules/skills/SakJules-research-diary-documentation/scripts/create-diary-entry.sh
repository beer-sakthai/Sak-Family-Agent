#!/usr/bin/env bash
# Script to help create and commit diary entries

set -e

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not in a git repository"
    exit 1
fi

# Check if diaries directory exists, create if not
if [ ! -d "diaries" ]; then
    echo "Creating diaries directory..."
    mkdir -p diaries
fi

# Get parameters
AGENT_NAME=${1:-"saksee"}
TOPIC=${2:-"research"}
DATE=$(date +%Y-%m-%d)

# Create agent directory if it doesn't exist
if [ ! -d "diaries/$AGENT_NAME" ]; then
    echo "Creating directory for $AGENT_NAME..."
    mkdir -p "diaries/$AGENT_NAME"
fi

# Create diary filename
FILENAME="diaries/$AGENT_NAME/${TOPIC// /-}-$DATE.md"

# Check if file already exists
if [ -f "$FILENAME" ]; then
    echo "Warning: $FILENAME already exists"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting..."
        exit 1
    fi
fi

# Create diary entry from template
cat > "$FILENAME" << EOF
# $TOPIC

**Date**: $DATE
**Author**: $AGENT_NAME
**Topic**: $TOPIC

## Research Objective

[What was the goal of this research?]

## Sources Consulted

- [Source 1](link)
- [Source 2](link)

## Key Findings

1. [Finding 1]
2. [Finding 2]
3. [Finding 3]

## Detailed Analysis

[In-depth analysis of findings, including any data, quotes, or observations]

## Conclusions

[What conclusions can be drawn from this research?]

## Next Steps

- [ ] Action item 1
- [ ] Action item 2

## References

- [Link to source](link)
- [Related documentation](link)
EOF

echo "Created diary entry: $FILENAME"

# Add to git
git add "$FILENAME"
echo "Added $FILENAME to git staging"

# Show status
git status --porcelain "$FILENAME"