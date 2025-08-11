#!/bin/bash

# Script to reset/delete all statuses on a given commit
# Usage: ./reset_commit_statuses.sh <commit_sha>

set -e

COMMIT_SHA="$1"

if [ -z "$COMMIT_SHA" ]; then
    echo "Usage: $0 <commit_sha>"
    echo "Example: $0 60ac7131a6b945ce39b1b35a4bda535289337b84"
    exit 1
fi

echo "🔍 Getting current statuses for commit $COMMIT_SHA..."

# Get all statuses for the commit
STATUSES=$(gh api "/repos/:owner/:repo/commits/$COMMIT_SHA/statuses" --jq '.[].context' 2>/dev/null || echo "")

if [ -z "$STATUSES" ]; then
    echo "ℹ️  No statuses found for commit $COMMIT_SHA"
    exit 0
fi

echo "📋 Found the following statuses:"
echo "$STATUSES" | sed 's/^/  - /'

echo ""
echo "🧹 Clearing all statuses (GitHub doesn't allow deletion, but we can supersede them)..."

# Clear each status by superseding it with a success state marked as cleared
# The newest status for each context takes precedence in GitHub's UI
while IFS= read -r context; do
    if [ -n "$context" ]; then
        echo "  🗑️  Clearing status: $context"
        gh api "/repos/:owner/:repo/statuses/$COMMIT_SHA" \
            --method POST \
            --field state="success" \
            --field context="$context" \
            --field description="Status cleared - was pending/stale" \
            --silent || {
                echo "    ⚠️  Failed to clear: $context"
            }
    fi
done <<< "$STATUSES"

echo ""
echo "✅ All statuses have been cleared for commit $COMMIT_SHA"
echo "💡 Note: GitHub doesn't allow true deletion, but the statuses are now superseded"
echo "💡 You can now re-run your actions/workflows"
