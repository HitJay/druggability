#!/bin/bash
# Sequential resumable downloader for Dryad humanPPI files (presigned S3 urls).
cd /das/user/QYJI/druggability/humanPPI_repro/downloads

python3 - <<'EOF' > dl_targets.sh
import json
urls = json.load(open('dryad_urls.json'))
order = ['RF2-PPI.pt','final_predictions.tar.gz','RF2-PPI_scores.gz','AF_scores.gz',
         'screened_pairs.tar.gz','DCA_scores.gz','protein_omicMSAs.tar.gz','segment_omicMSAs.tar.gz']
for name in order:
    print(f'{name}\t{urls[name]}')
EOF

while IFS=$'\t' read -r name url; do
  if [ -f "$name.ok" ]; then echo "SKIP $name (already done)"; continue; fi
  echo "==== $(date '+%F %T') START $name"
  rc=1
  for try in 1 2 3 4 5 6 7 8; do
    curl -sS -o "$name" -C - --max-time 14400 "$url" && rc=0 && break
    rc=$?
    echo "---- retry $try rc=$rc $(date '+%F %T')"
    sleep 10
  done
  echo "==== $(date '+%F %T') END $name rc=$rc size=$(stat -c%s "$name" 2>/dev/null)"
  if [ $rc -eq 0 ]; then touch "$name.ok"; fi
done < dl_targets.sh
echo "ALL_DOWNLOADS_FINISHED"
