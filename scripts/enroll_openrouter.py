"""Enroll a model through OpenRouter, pinned to the model maker's own provider.

usage:
  OPENROUTER_API_KEY=... python scripts/enroll_openrouter.py \
      --model z-ai/glm-5.3 --label glm-5.3 --provider z-ai --served-by "Z.AI"

Every request sets provider.only to the maker's provider slugs with
allow_fallbacks false, and an answer whose response names any other provider is
discarded, so third-party hosts (often quantized) never enter the bank. The
provider that actually answered is kept in each row's served_by field. Appends
the strict-valid answers of ModelTrace's fixed 36-task suite to
reference/<label>.jsonl; --count below 36 runs a smoke test that only prints.
The key is read from OPENROUTER_API_KEY and is never written to disk.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UPSTREAM = ROOT / "upstream" / "ModelTrace"
if not (UPSTREAM / "enrollment.py").exists():
    raise SystemExit("upstream/ModelTrace is empty: run `git submodule update --init` first")
sys.path.insert(0, str(UPSTREAM))

from challenge_suite import fingerprint_suite  # noqa: E402
from enrollment import make_row  # noqa: E402

parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
parser.add_argument("--model", required=True, help="OpenRouter model id, e.g. z-ai/glm-5.3")
parser.add_argument("--label", required=True, help="bank label, starting with the family: glm-, kimi-, gemini-, grok-, ...")
parser.add_argument("--provider", required=True, help="the maker's OpenRouter provider slugs, comma separated, e.g. z-ai")
parser.add_argument("--served-by", required=True, help="provider names accepted in the response, comma separated, e.g. 'Z.AI'")
parser.add_argument("--count", type=int, default=36, help="below 36: smoke test with one task, prints only")
args = parser.parse_args()

key = os.environ.get("OPENROUTER_API_KEY", "").strip()
if not key:
    raise SystemExit("set OPENROUTER_API_KEY")
pin = [slug.strip() for slug in args.provider.split(",")]
allowed = {name.strip().lower() for name in args.served_by.split(",")}


def ask(task: dict) -> tuple[dict | None, str]:
    prompt = task["prompt"]
    if task["user_prefix"]:
        prompt = task["user_prefix"] + "\n\nFinal task:\n" + prompt
    messages = ([{"role": "system", "content": task["system"]}] if task["system"] else []) + [{"role": "user", "content": prompt}]
    body = {"model": args.model, "messages": messages, "provider": {"only": pin, "allow_fallbacks": False}, "usage": {"include": True}}
    last = ""
    for attempt in range(3):
        request = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                     "HTTP-Referer": "https://github.com/SPHINX998/modeltrace-bank", "X-Title": "modeltrace-bank enrollment"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=600) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            last = f"HTTP {error.code}: {error.read().decode('utf-8', 'replace')[:300]}"
            time.sleep(2 * (attempt + 1))
            continue
        except Exception as error:  # noqa: BLE001
            last = str(error)
            time.sleep(2 * (attempt + 1))
            continue
        if payload.get("error") or not payload.get("choices"):
            last = f"error body: {json.dumps(payload.get('error') or payload, ensure_ascii=False)[:300]}"
            time.sleep(2 * (attempt + 1))
            continue
        provider = str(payload.get("provider", ""))
        if provider.lower() not in allowed:
            return None, f"{task['challenge_id']}: served by {provider!r}, not first party"
        choice = payload["choices"][0]
        content = choice["message"].get("content") or ""
        if isinstance(content, list):
            content = "".join(part.get("text", "") for part in content)
        if choice.get("finish_reason") in {"length", "content_filter"}:
            last = f"finish_reason {choice.get('finish_reason')}"
            continue
        row = make_row(
            model_label=args.label, text=content, condition=task["condition"], challenge_id=task["challenge_id"],
            expected_count=task["expected_count"], temperature="provider_default", bank_id="pinai-official",
            wrapper_transport=task["transport"], provider=f"official:{args.model}", prompt=prompt,
            base_prompt=task["prompt"], system_prompt=task["system"], user_prefix=task["user_prefix"],
        )
        row["served_by"] = provider
        usage = payload.get("usage") or {}
        row["usage"] = {name: usage.get(name) for name in ("prompt_tokens", "completion_tokens", "cost")}
        if row["strict_valid"]:
            return row, ""
        last = f"parsed {row['parsed_count']}/{row['strict_threshold']}"
    return None, f"{task['challenge_id']}: {last}"


suite = fingerprint_suite()
tasks = suite if args.count >= len(suite) else [suite[0]]
rows, errors = [], []
with ThreadPoolExecutor(max_workers=3) as pool:
    for future in as_completed([pool.submit(ask, task) for task in tasks]):
        row, error = future.result()
        if row is not None:
            rows.append(row)
        if error:
            errors.append(error)
cost = sum((row["usage"].get("cost") or 0) for row in rows)
if args.count < len(suite):
    for row in rows:
        print(json.dumps({"label": args.label, "served_by": row["served_by"], "parsed": row["parsed_count"],
                          "expected": row["requested_count"], "usage": row["usage"], "head": row["text"][:80]}, ensure_ascii=False))
    print(json.dumps({"label": args.label, "errors": errors}, ensure_ascii=False))
    sys.exit(0)
with (ROOT / "reference" / f"{args.label}.jsonl").open("a", encoding="utf-8") as handle:
    for row in sorted(rows, key=lambda item: item["challenge_id"]):
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
print(json.dumps({"label": args.label, "accepted": len(rows), "errors": errors, "cost_usd": round(cost, 4)}, ensure_ascii=False))
