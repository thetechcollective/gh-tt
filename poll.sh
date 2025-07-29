#!/usr/bin/env bash
# filepath: /workspaces/lakruzz.com/poll.sh

STATUSES=spell-check,markdown-linting,jekyll-build
INTERVAL=4 # Polling interval in seconds

# Convert comma-separated list to array
IFS=',' read -ra STATUS_ARRAY <<< "$STATUSES"

echo "Polling commit $(git rev-parse --short HEAD) for statuses ever $INTERVAL seconds..."
echo "Press Ctrl+C to stop polling" - will exit when all check are done.
echo
echo
echo
echo
echo

while true; do
    # Get current status data
    STATUS_DATA=$(gh api repos/lakruzz/lakruzz.com/commits/$(git rev-parse HEAD)/status 2>/dev/null)
    
    if [ $? -ne 0 ]; then
        # Move cursor up 4 lines and overwrite
        echo -ne "\033[4A"
        echo "Failed to fetch status data$(printf '%*s' 50 '')"
        echo "$(printf '%*s' 70 '')"
        echo "$(printf '%*s' 70 '')"
        echo "$(printf '%*s' 70 '')"
        sleep $INTERVAL
        continue
    fi
    
    ALL_SET=true
    ALL_SUCCESS=true
    
    # Move cursor up 4 lines
    echo -ne "\033[4A"
    
    # First line: timestamp
    echo "Last check $(date '+%H:%M:%S')$(printf '%*s' 30 '')"
    
    # Lines 2-4: status results (pad with spaces to clear any leftover text)
    for status in "${STATUS_ARRAY[@]}"; do
        STATE=$(echo "$STATUS_DATA" | jq -r --arg context "$status" '
            .statuses[] 
            | select(.context == $context) 
            | .state
        ' 2>/dev/null)
        
        if [ -z "$STATE" ] || [ "$STATE" = "null" ]; then
            echo "   ❓ $status:  [unset]$(printf '%*s' 40 '')"
            ALL_SET=false
        else
            case "$STATE" in
                "success") STATUS_ICON="✅" ;;
                "failure") STATUS_ICON="❌" ;;
                "error") STATUS_ICON="💥" ;;
                "pending") STATUS_ICON="⏳" ;;
                *) STATUS_ICON="❓" ;;
            esac
            echo "   $STATUS_ICON $status: [$STATE]$(printf '%*s' 40 '')"
            if [ "$STATE" != "success" ]; then
                ALL_SUCCESS=false
            fi
        fi
    done
    
    # Check if all statuses are set
    if [ "$ALL_SET" = true ]; then
#        echo -ne "\033[4A"
        if [ "$ALL_SUCCESS" = true ]; then
            echo "✅ All checks passed! $(printf '%*s' 40 '')"
        else
            echo "❌ Some checks failed! $(printf '%*s' 40 '')"
        fi
        echo "$(printf '%*s' 70 '')"
        echo "$(printf '%*s' 70 '')"
        echo "$(printf '%*s' 70 '')"
        
        if [ "$ALL_SUCCESS" = true ]; then
            exit 0
        else
            exit 1
        fi
    fi
    
    sleep $INTERVAL
done