#!/bin/bash
# Watchdog: wait for scoring (04) to finish, then run evaluation (05), then report.
# Resumable-safe: 04 already skips complete shards; 05 is idempotent.
set -u
ROOT=/das/user/QYJI/druggability/humanPPI_repro
cd $ROOT
LOG=$ROOT/logs/watchdog_eval.log
exec >> $LOG 2>&1

echo "==== watchdog start $(date)"

# 1) wait for the running scoring orchestrator to exit (check every 2 min, max 6h)
for i in $(seq 1 180); do
  if ! pgrep -f "scripts/04_score_rf2ppi.py" > /dev/null; then
    echo "scoring process exited at $(date)"
    break
  fi
  sleep 120
done

if pgrep -f "scripts/04_score_rf2ppi.py" > /dev/null; then
  echo "ERROR: scoring still running after 6h watchdog window; aborting (will not double-launch)"
  exit 1
fi

# 2) count scored pairs; if incomplete, try one resume round of 04 (max 2 rounds)
source /data/user/QYJI/miniforge3/etc/profile.d/conda.sh
conda activate rf2ppi
export PATH=$ROOT/external/hhsuite:$PATH
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
export PYTHONPATH=$ROOT/work/patch

EXPECTED=33000
for round in 1 2; do
  N=$(cat $ROOT/work/pair_lists/*.log 2>/dev/null | grep -v Input_MSA | wc -l)
  echo "round $round: scored $N/$EXPECTED"
  if [ "$N" -ge "$EXPECTED" ]; then break; fi
  echo "resuming scoring (round $round)"
  python scripts/04_score_rf2ppi.py 0,1,2,3,4,5 1
done

N=$(cat $ROOT/work/pair_lists/*.log 2>/dev/null | grep -v Input_MSA | wc -l)
echo "final scored count: $N/$EXPECTED"

# 3) run evaluation regardless (05 handles missing pairs by reporting them)
echo "==== running 05_evaluate"
python scripts/05_evaluate.py
EVAL_RC=$?
echo "eval exit: $EVAL_RC"

# 4) verify outputs
ls -la $ROOT/results/ | grep -E "pr_curve|pr_metrics|crosscheck" || echo "WARN: results missing"
echo "==== watchdog done $(date)"
if [ $EVAL_RC -eq 0 ]; then echo WATCHDOG_ALL_DONE; else echo WATCHDOG_EVAL_FAILED; fi
