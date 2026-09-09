#!/bin/bash
# Sequential baselines (parallel runs were OOM-killed by the cgroup at ~5.6 GB combined).
cd /home/claude/project
for c in WP2024s42 WP2033s42 WP2033s43; do
  python3 src/run_engine.py $c baseline >> out/logs/${c}_baseline.log 2>&1
  echo "[$c] baseline exit $?" >> out/logs/chain.log
done
