#!/bin/bash
# Monitor batch progress

cd "$(dirname "$0")"

while true; do
  if [ -f batch_results_optimized.txt ]; then
    count=$(grep -c "^\[" batch_results_optimized.txt 2>/dev/null || echo 0)
    echo "[$(date '+%H:%M:%S')] Progress: $count/270 instances"
    echo "Last 3 lines:"
    tail -3 batch_results_optimized.txt
  else
    echo "Waiting for batch_results_optimized.txt..."
  fi
  echo ""
  sleep 10
done
