# modeltrace-bank · 扩展模型指纹库

An extended, reproducible fingerprint bank for [ModelTrace](https://github.com/xqy2006/ModelTrace): upstream GPT + Claude, plus DeepSeek, GLM, Kimi, Gemini and Grok enrolled from first-party providers only, with the same 36-task suite. Drop-in replacement for ModelTrace's `data/unified_bank.json`.

[ModelTrace](https://github.com/xqy2006/ModelTrace) 兼容的扩展指纹库：在上游 GPT（8 个）和 Claude（10 个）的基础上，加入按同一套 36 道题、只从**原厂服务**采集的 DeepSeek、GLM、Kimi、Gemini、Grok 参考答案，重新拟合成一个统一库。`bank/unified_bank.json` 与 ModelTrace 的 `data/unified_bank.json` 格式相同，替换后 ModelTrace 就能在这些家族之间一起判断。

适合用来判断一个 API 渠道（中转、聚合平台、自建网关）实际返回的是不是它声称的模型。

## 收录模型

| 家族 | 模型 | 参考答案来源 |
|---|---|---|
| GPT | gpt-5.4、gpt-5.5、gpt-5.6-sol、gpt-5.6-terra、gpt-5.6-luna、gpt-6-astra、gpt-6-sol、gpt-6-luna | 上游 ModelTrace（原样引用） |
| Claude | claude-haiku-4-5-20251001、claude-haiku-5-5、claude-sonnet-4-6、claude-sonnet-5、claude-sonnet-5-5、claude-opus-4-6、claude-opus-4-7、claude-opus-4-8、claude-opus-5、claude-opus-5-5 | 上游 ModelTrace（原样引用） |
| DeepSeek | deepseek-v4.1-flash、deepseek-v4-pro | DeepSeek 官方 API（`deepseek-flash`、`deepseek-v4-pro`）。采集当日 `deepseek-flash` 由 DeepSeek-V4.1-Flash-1017 提供 |
| GLM | glm-5.3、glm-5.3-flash | OpenRouter，固定原厂 provider Z.AI |
| Kimi | kimi-k2.6、kimi-k3 | OpenRouter，固定原厂 provider Moonshot AI |
| Gemini | gemini-3.8-flash | OpenRouter，固定原厂 provider Google |
| Grok | grok-4.6、grok-4.7 | OpenRouter，固定原厂 provider xAI |

新增模型均于 2026-10-23 采集，每个模型 36 份回答。

只收原厂服务的回答。经 OpenRouter 采集时，每个请求都用 `provider.only` 固定原厂并关闭回落（`allow_fallbacks: false`），响应里服务方不是原厂的回答直接丢弃，实际服务方记在每行的 `served_by` 字段。这一点对 GLM、Kimi 尤其重要：OpenRouter 上它们有大量第三方托管，其中不少是量化版本。`provider` 字段里的 `official:` 表示原厂服务，不表示直连原厂接口。

## 准确率

留一题交叉验证：每次留出一道题，用其余题拟合，再判断留出那道题的回答属于库里哪个模型。

| 每次判断用几份回答 | 准确率 |
|---|---|
| 1 | 93.6% |
| 2 | 99.6% |
| 3 | 100% |

逐模型结果和主要误判去向见 [ACCURACY.md](ACCURACY.md)。

需要知道的局限：

- 这是参考数据内部的准确率。真实渠道加了系统提示词、改了采样参数或套了客户端时，准确率通常更低；上游已知在 Claude Code 里测偏差较大。
- 闭集判断：库里没有的模型也会被判成最像的那个。
- 结果只是参考证据，不是定论。

## 使用

### 直接替换 ModelTrace 的库

```bash
git clone https://github.com/xqy2006/ModelTrace
git clone https://github.com/SPHINX998/modeltrace-bank
cp modeltrace-bank/bank/unified_bank.json ModelTrace/data/unified_bank.json
cd ModelTrace
pip install -r requirements.txt
python start.py
```

在 ModelTrace 网页里「添加模型指纹」会按它自己 `data/` 下的数据重建统一库，覆盖替换进去的文件。

### 自己重建

```bash
git clone --recursive https://github.com/SPHINX998/modeltrace-bank
cd modeltrace-bank
pip install -r upstream/ModelTrace/requirements.txt
python scripts/build_bank.py
```

生成 `bank/unified_bank.json` 和 `ACCURACY.md`。`upstream/ModelTrace` 是指向上游固定提交的 submodule，建库代码和 GPT/Claude 参考答案都从那里读。

### 采集新模型

原厂官方 API：

```bash
export MODELTRACE_API_KEY=...
python scripts/enroll_official.py --base-url https://api.deepseek.com --model deepseek-flash --label deepseek-v4.1-flash
```

经 OpenRouter 固定原厂：

```bash
export OPENROUTER_API_KEY=...
python scripts/enroll_openrouter.py --model z-ai/glm-5.3 --label glm-5.3 --provider z-ai --served-by "Z.AI"
```

采集结果追加到 `reference/<label>.jsonl`，再跑一次 `scripts/build_bank.py`。`--label` 以家族名开头（gpt-、claude-、deepseek-、glm-、kimi-、gemini-、grok-）。Key 只从环境变量读取，不写入任何文件。欢迎提交从原厂服务采集的新模型。

## 目录

```text
reference/              新增模型的参考答案，一个模型一个 jsonl
bank/unified_bank.json  生成的统一库
ACCURACY.md             生成的交叉验证准确率
scripts/                建库与采集脚本
upstream/ModelTrace     上游 ModelTrace（submodule，原样引用）
```

## 关于 PinAI

这个扩展库是 [PinAI](https://app.pinaic.com) 在做模型真伪检测时整理出来的。PinAI 是一家 AI 模型 API 中转站。我们自己也用同一套方法持续抽测线上服务，结果放在一个**不用登录就能看**的[模型页](https://app.pinaic.com/models)：每个模型、每个分组近 1 小时的降智率，以及缓存命中率、延迟和实际单价。目前降智率覆盖 GPT 各分组。

把库开源，是因为一个渠道给的是不是真模型，不该只由渠道自己说了算。你可以拿它去测任何一家，包括 PinAI。测出问题，欢迎在 issue 里贴结果。

## 许可与致谢

MIT，见 [LICENSE](LICENSE)。

- 指纹方法、36 道挑战题、建库代码和 GPT/Claude 参考答案来自 [xqy2006/ModelTrace](https://github.com/xqy2006/ModelTrace)（MIT，Copyright (c) 2026 xqy2006），以 submodule 原样引用，未修改。
- 一并感谢 ModelTrace 致谢的 [hanlinwenyuan/hlwy-ai-checker](https://github.com/hanlinwenyuan/hlwy-ai-checker)：它较早把模型随机数字偏差用于 API 渠道一致性检查。
