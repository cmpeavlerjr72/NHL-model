#!/usr/bin/env bash
# Box bootstrap (Lane O). Runs ON the box as root, called from user-data after the repo is cloned.
# Installs Python 3.12 venv + repo deps, pins thread env vars to vCPU count, pulls inputs from HF.
# Env in (from user-data): HF_TOKEN, REQ_INPUTS (extra args for hf_sync_data.py pull, may be empty), REQ_EXTRAS (pip extras, default sim,dev)
set -uo pipefail
cd "$(dirname "$0")/.."
N=$(nproc)
cat > /etc/profile.d/nhl_threads.sh <<EOT
export OMP_NUM_THREADS=$N MKL_NUM_THREADS=$N OPENBLAS_NUM_THREADS=$N NUMEXPR_NUM_THREADS=$N PYTHONIOENCODING=utf-8
EOT
. /etc/profile.d/nhl_threads.sh
dnf install -y python3.12 python3.12-pip >/dev/null 2>&1 || { echo "dnf python3.12 failed"; exit 11; }
python3.12 -m venv .venv || exit 12
. .venv/bin/activate
pip install -q --upgrade pip
pip install -q -e ".[${REQ_EXTRAS:-sim,dev}]" || { echo "pip install failed"; exit 13; }
if [ -n "${REQ_INPUTS:-}" ]; then
  # shellcheck disable=SC2086
  python scripts/hf_sync_data.py pull ${REQ_INPUTS} --max-attempts 6 || { echo "hf pull failed"; exit 14; }
fi
echo "bootstrap ok vcpu=$N $(python --version)"
