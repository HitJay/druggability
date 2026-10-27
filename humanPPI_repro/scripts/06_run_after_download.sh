#!/bin/bash
# Post-download pipeline: extract protein_omicMSAs, point single-MSA dir, run pMSA gen.
set -e
ROOT=/das/user/QYJI/druggability/humanPPI_repro
cd $ROOT

if [ ! -f downloads/protein_omicMSAs.tar.gz.ok ]; then echo "protein_omicMSAs not ready"; exit 1; fi
if [ ! -d work/single_msas ]; then
  echo "==== extracting protein_omicMSAs.tar.gz -> work/single_msas"
  mkdir -p work/single_msas_extract
  tar xzf downloads/protein_omicMSAs.tar.gz -C work/single_msas_extract
  # find the directory that actually contains *.a3m
  MSDIR=$(dirname "$(find work/single_msas_extract -name '*.a3m' | head -1)")
  ln -s "$(readlink -f $MSDIR)" work/single_msas
  echo "single_msas -> $MSDIR ($(ls $MSDIR/*.a3m | wc -l) files)"
fi

export PATH=$ROOT/external/hhsuite:$PATH
source /data/user/QYJI/miniforge3/etc/profile.d/conda.sh
conda activate rf2ppi
echo "==== generating paired MSAs (32 parallel shards)"
python scripts/03_generate_pmsa.py 32

echo "==== RF2-PPI scoring on GPUs 0-5"
python scripts/04_score_rf2ppi.py 0,1,2,3,4,5 4

echo "==== evaluation"
python scripts/05_evaluate.py
echo PIPELINE_DONE
