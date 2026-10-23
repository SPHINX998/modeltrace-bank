"""Enroll a model from its maker's own API with ModelTrace's fixed 36-task suite.

usage:
  MODELTRACE_API_KEY=... python scripts/enroll_official.py \
      --base-url https://api.deepseek.com --model deepseek-flash --label deepseek-v4.1-flash

Appends the strict-valid answers to reference/<label>.jsonl. Only point this at
the model maker's own API; answers from other services belong elsewhere. The key
is read from MODELTRACE_API_KEY and is never written to disk.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UPSTREAM = ROOT / "upstream" / "ModelTrace"
if not (UPSTREAM / "enrollment.py").exists():
    raise SystemExit("upstream/ModelTrace is empty: run `git submodule update --init` first")
sys.path.insert(0, str(UPSTREAM))

import enrollment  # noqa: E402

parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
parser.add_argument("--base-url", required=True, help="the maker's API base URL")
parser.add_argument("--model", required=True, help="model name as the API calls it")
parser.add_argument("--label", required=True, help="bank label, starting with the family: gpt-, claude-, deepseek-, glm-, kimi-, gemini-, grok-")
parser.add_argument("--format", choices=("openai", "anthropic"), default="openai", help="API format (default openai)")
args = parser.parse_args()

key = os.environ.get("MODELTRACE_API_KEY", "").strip()
if not key:
    raise SystemExit("set MODELTRACE_API_KEY")

# Only collect here; scripts/build_bank.py fits the bank.
enrollment.rebuild_bank = lambda *_args, **_kwargs: {"models": []}
enrollment.bank_summary = lambda _bank: {}

result = enrollment.enroll_automatic(
    base_url=args.base_url,
    api_key=key,
    api_model=args.model,
    model_label=args.label,
    sample_count=36,
    temperature=None,
    api_format=args.format,
    data_file=ROOT / "reference" / f"{args.label}.jsonl",
    bank_file=ROOT / "reference" / "unused_bank.json",
    bank_id="pinai-official",
    provider=f"official:{args.model}",
)
result.pop("bank", None)
print(json.dumps(result, ensure_ascii=False, indent=2))
