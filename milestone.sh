#!/bin/bash

# Script to create the same milestone across multiple repositories
# Usage: ./milestone.sh

MILESTONE_TITLE="feature A"
DUE_DATE="2025-08-15"
REPOS=("R-one" "R-two")

echo "Creating milestone '$MILESTONE_TITLE' with due date '$DUE_DATE' in repositories:"

for repo in "${REPOS[@]}"; do
    echo "  - $repo"
    gh milestone create "$MILESTONE_TITLE" \
        --repo "thetechcollective/$repo" \
        --due-date "$DUE_DATE" \
        --description "Feature A milestone" || echo "    ⚠️  Failed to create milestone in $repo (might already exist)"
done

echo "✅ Milestone creation completed!"

# Alternative one-liner approach (commented out):
# for repo in R-one R-two; do gh milestone create "feature A" --repo "thetechcollective/$repo" --due-date "2025-08-15"; done
