# 交叉验证准确率

由 `scripts/build_bank.py` 生成，请勿手改。

口径：留一题交叉验证。每次留出一道题（两份回答时留出同一环境下的两道题），用其余题拟合指纹库，再判断留出题的回答属于库里哪个模型。这是参考数据内部的准确率；真实渠道加了系统提示词、改了采样参数或套了客户端时，准确率通常更低。

上游数据：xqy2006/ModelTrace @ `6cd4a8f`。共 27 个模型、972 份回答。

## 整体

| 每次判断用几份回答 | 准确率 |
|---|---|
| 1 | 910/972（93.6%） |
| 2 | 968/972（99.6%） |
| 3 | 324/324（100.0%） |

## 逐模型

| 家族 | 模型 | 参考答案来源 | 1 份回答 | 2 份回答 | 1 份回答时误判为 |
|---|---|---|---|---|---|
| GPT | gpt-5.4 | 上游 ModelTrace | 30/36（83.3%） | 35/36（97.2%） | gpt-6-astra ×2、claude-opus-5-5 ×2、gpt-6-sol ×1、gpt-6-luna ×1 |
| GPT | gpt-5.5 | 上游 ModelTrace | 34/36（94.4%） | 36/36（100.0%） | gpt-6-luna ×1、gpt-5.6-sol ×1 |
| GPT | gpt-5.6-sol | 上游 ModelTrace | 34/36（94.4%） | 36/36（100.0%） | kimi-k3 ×1、deepseek-v4-pro ×1 |
| GPT | gpt-5.6-terra | 上游 ModelTrace | 36/36（100.0%） | 36/36（100.0%） | — |
| GPT | gpt-5.6-luna | 上游 ModelTrace | 36/36（100.0%） | 36/36（100.0%） | — |
| GPT | gpt-6-astra | 上游 ModelTrace | 34/36（94.4%） | 36/36（100.0%） | gpt-6-sol ×2 |
| GPT | gpt-6-sol | 上游 ModelTrace | 33/36（91.7%） | 36/36（100.0%） | gpt-6-luna ×1、gpt-6-astra ×1、gpt-5.6-sol ×1 |
| GPT | gpt-6-luna | 上游 ModelTrace | 36/36（100.0%） | 36/36（100.0%） | — |
| Claude | claude-haiku-4-5-20251001 | 上游 ModelTrace | 35/36（97.2%） | 36/36（100.0%） | gemini-3.8-flash ×1 |
| Claude | claude-sonnet-4-6 | 上游 ModelTrace | 36/36（100.0%） | 36/36（100.0%） | — |
| Claude | claude-sonnet-5 | 上游 ModelTrace | 30/36（83.3%） | 36/36（100.0%） | grok-4.6 ×3、claude-opus-4-7 ×1、claude-haiku-4-5-20251001 ×1、claude-opus-5 ×1 |
| Claude | claude-opus-4-6 | 上游 ModelTrace | 36/36（100.0%） | 36/36（100.0%） | — |
| Claude | claude-opus-4-7 | 上游 ModelTrace | 34/36（94.4%） | 36/36（100.0%） | claude-opus-4-8 ×1、gemini-3.8-flash ×1 |
| Claude | claude-opus-4-8 | 上游 ModelTrace | 30/36（83.3%） | 35/36（97.2%） | claude-opus-4-7 ×3、claude-opus-5 ×2、grok-4.6 ×1 |
| Claude | claude-opus-5 | 上游 ModelTrace | 36/36（100.0%） | 36/36（100.0%） | — |
| Claude | claude-opus-5-5 | 上游 ModelTrace | 36/36（100.0%） | 36/36（100.0%） | — |
| Claude | claude-sonnet-5-5 | 上游 ModelTrace | 36/36（100.0%） | 36/36（100.0%） | — |
| Claude | claude-haiku-5-5 | 上游 ModelTrace | 36/36（100.0%） | 36/36（100.0%） | — |
| DeepSeek | deepseek-v4-pro | 原厂官方 API | 32/36（88.9%） | 36/36（100.0%） | gpt-5.5 ×2、kimi-k3 ×1、claude-opus-4-6 ×1 |
| DeepSeek | deepseek-v4.1-flash | 原厂官方 API | 32/36（88.9%） | 35/36（97.2%） | gpt-5.5 ×2、gemini-3.8-flash ×1、gpt-5.6-sol ×1 |
| Gemini | gemini-3.8-flash | OpenRouter · Google | 35/36（97.2%） | 36/36（100.0%） | gpt-6-astra ×1 |
| GLM | glm-5.3-flash | OpenRouter · Z.AI | 30/36（83.3%） | 36/36（100.0%） | claude-haiku-5-5 ×2、claude-opus-5 ×2、glm-5.3 ×1、gpt-5.6-terra ×1 |
| GLM | glm-5.3 | OpenRouter · Z.AI | 36/36（100.0%） | 36/36（100.0%） | — |
| Grok | grok-4.6 | OpenRouter · xAI | 29/36（80.6%） | 35/36（97.2%） | claude-opus-4-6 ×2、claude-opus-5-5 ×2、deepseek-v4.1-flash ×1、kimi-k2.6 ×1、kimi-k3 ×1 |
| Grok | grok-4.7 | OpenRouter · xAI | 35/36（97.2%） | 36/36（100.0%） | gpt-5.4 ×1 |
| Kimi | kimi-k2.6 | OpenRouter · Moonshot AI | 32/36（88.9%） | 36/36（100.0%） | gpt-5.5 ×1、grok-4.6 ×1、grok-4.7 ×1、claude-opus-4-6 ×1 |
| Kimi | kimi-k3 | OpenRouter · Moonshot AI | 31/36（86.1%） | 36/36（100.0%） | claude-opus-5-5 ×1、gpt-5.5 ×1、gpt-6-sol ×1、claude-opus-5 ×1、kimi-k2.6 ×1 |
