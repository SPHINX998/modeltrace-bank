"""Rebuild bank/unified_bank.json and ACCURACY.md.

usage: python scripts/build_bank.py

Fits one ModelTrace bank from the upstream GPT and Claude reference answers
(upstream/ModelTrace/data/*_reference.jsonl, used as is) plus every file in
reference/, with ModelTrace's own bank_builder, then writes the per-model
leave-one-challenge-out accuracy to ACCURACY.md.
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UPSTREAM = ROOT / "upstream" / "ModelTrace"
if not (UPSTREAM / "bank_builder.py").exists():
    raise SystemExit("upstream/ModelTrace is empty: run `git submodule update --init` first")
sys.path.insert(0, str(UPSTREAM))

from bank_builder import build_bank, calibration_records, read_rows  # noqa: E402

FAMILIES = {
    "gpt": "GPT",
    "claude": "Claude",
    "deepseek": "DeepSeek",
    "glm": "GLM",
    "kimi": "Kimi",
    "gemini": "Gemini",
    "grok": "Grok",
}
UPSTREAM_FILES = {"gpt": "gpt_reference.jsonl", "claude": "claude_reference.jsonl"}


def family_of(label: str) -> str:
    for family in FAMILIES:
        if label.startswith(family + "-"):
            return family
    raise SystemExit(f"reference/{label}.jsonl: file name must start with one of {', '.join(f + '-' for f in FAMILIES)}")


revision = subprocess.run(
    ["git", "-C", str(UPSTREAM), "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True
).stdout.strip()

rows: list[dict] = []
origin: dict[str, str] = {}
for family, name in UPSTREAM_FILES.items():
    for row in read_rows(UPSTREAM / "data" / name):
        rows.append({**row, "family_id": family, "family_name": FAMILIES[family]})
        origin[row["source"]] = "上游 ModelTrace"
for path in sorted((ROOT / "reference").glob("*.jsonl")):
    family = family_of(path.stem)
    enrolled = read_rows(path)
    for row in enrolled:
        if row["source"] != path.stem:
            raise SystemExit(f"{path.name}: row labelled {row['source']!r}, expected {path.stem!r}")
        if not str(row.get("provider", "")).startswith("official:"):
            raise SystemExit(f"{path.name}: provider {row.get('provider')!r} is not a first-party source (official:<model>)")
        rows.append({**row, "family_id": family, "family_name": FAMILIES[family]})
    served = sorted({row["served_by"] for row in enrolled if row.get("served_by")})
    origin[path.stem] = f"OpenRouter · {' / '.join(served)}" if served else "原厂官方 API"

bank = build_bank(rows)
# The upstream rows name the service upstream collected them from; this bank
# credits them to the upstream dataset instead.
bank["providers"] = [f"upstream:xqy2006/ModelTrace@{revision}"] + sorted(
    {row["provider"] for row in rows if str(row.get("provider", "")).startswith("official:")}
)
bank["source_scope"] = (
    f"GPT and Claude reference outputs from xqy2006/ModelTrace @ {revision} (MIT License, Copyright (c) 2026 xqy2006); "
    "other families enrolled from first-party providers with the same 36-task suite, see reference/."
)
(ROOT / "bank").mkdir(exist_ok=True)
(ROOT / "bank" / "unified_bank.json").write_text(json.dumps(bank, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

model_ids = bank["robust"]["model_order"]
family = {model["id"]: model["family_name"] for model in bank["models"]}
per_model: dict[str, dict] = defaultdict(dict)
for query_count in (1, 2):
    right, total = Counter(), Counter()
    confused: dict[str, Counter] = defaultdict(Counter)
    for scores, truth in calibration_records(rows, model_ids, query_count):
        predicted = max(range(len(scores)), key=scores.__getitem__)
        total[model_ids[truth]] += 1
        if predicted == truth:
            right[model_ids[truth]] += 1
        else:
            confused[model_ids[truth]][model_ids[predicted]] += 1
    for model in model_ids:
        per_model[model][query_count] = (right[model], total[model])
        if query_count == 1:
            per_model[model]["confused"] = confused[model]


def share(right: int, total: int) -> str:
    return f"{right}/{total}（{right / total:.1%}）" if total else "—"


lines = [
    "# 交叉验证准确率",
    "",
    "由 `scripts/build_bank.py` 生成，请勿手改。",
    "",
    "口径：留一题交叉验证。每次留出一道题（两份回答时留出同一环境下的两道题），用其余题拟合指纹库，再判断留出题的回答属于库里哪个模型。"
    "这是参考数据内部的准确率；真实渠道加了系统提示词、改了采样参数或套了客户端时，准确率通常更低。",
    "",
    f"上游数据：xqy2006/ModelTrace @ `{revision}`。共 {len(model_ids)} 个模型、{len(rows)} 份回答。",
    "",
    "## 整体",
    "",
    "| 每次判断用几份回答 | 准确率 |",
    "|---|---|",
]
for key, value in sorted(bank["calibration"].items(), key=lambda item: int(item[0])):
    lines.append(f"| {key} | {share(value['cv_correct'], value['cv_samples'])} |")
lines += [
    "",
    "## 逐模型",
    "",
    "| 家族 | 模型 | 参考答案来源 | 1 份回答 | 2 份回答 | 1 份回答时误判为 |",
    "|---|---|---|---|---|---|",
]
for model in model_ids:
    stats = per_model[model]
    mistakes = "、".join(f"{other} ×{count}" for other, count in stats["confused"].most_common()) or "—"
    lines.append(f"| {family[model]} | {model} | {origin[model]} | {share(*stats[1])} | {share(*stats[2])} | {mistakes} |")
(ROOT / "ACCURACY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

print(json.dumps({
    "models": len(model_ids),
    "responses": len(rows),
    "upstream": revision,
    "calibration": {key: round(value["cv_accuracy"], 4) for key, value in bank["calibration"].items()},
}, ensure_ascii=False))
