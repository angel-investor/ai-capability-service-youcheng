# AI Capability Service

一个 production-ready 的"模型能力统一调用"后端服务，基于 **FastAPI** 实现，接入 **DeepSeek API**。

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

复制 `.env.example` 为 `.env`，并填入你的 DeepSeek API Key：

```bash
cp .env.example .env
```

编辑 `.env`：

```
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

> 前往 [DeepSeek Platform](https://platform.deepseek.com) 获取 API Key。

### 3. 启动服务

```bash
uvicorn app.main:app --reload --port 8000
```

服务启动后访问：
- **API 文档（Swagger UI）**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/

---

## 接口说明

### POST `/v1/capabilities/run`

#### 支持的 capability

| capability | 描述 | 必填字段 | 可选字段 |
|---|---|---|---|
| `text_summary` | 文本摘要 | `text` (str) | `max_length` (int, 默认 120) |
| `sentiment_analysis` | 情感分析 | `text` (str) | - |

---

## 示例 curl 请求

### 文本摘要（text_summary）

```bash
curl -X POST http://localhost:8000/v1/capabilities/run \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "text_summary",
    "input": {
      "text": "人工智能（AI）是计算机科学的一个广泛分支，旨在构建能够执行通常需要人类智能的任务的系统。这些任务包括视觉感知、语音识别、决策和语言翻译。",
      "max_length": 50
    },
    "request_id": "demo-001"
  }'
```

**成功响应：**

```json
{
  "ok": true,
  "data": {
    "result": "AI 是模拟人类智能的计算机科学分支，涵盖视觉、语音、决策等任务。"
  },
  "meta": {
    "request_id": "demo-001",
    "capability": "text_summary",
    "elapsed_ms": 843
  }
}
```

---

### 情感分析（sentiment_analysis）

```bash
curl -X POST http://localhost:8000/v1/capabilities/run \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "sentiment_analysis",
    "input": {
      "text": "This product is absolutely amazing! Highly recommended."
    },
    "request_id": "demo-002"
  }'
```

**成功响应：**

```json
{
  "ok": true,
  "data": {
    "result": {
      "sentiment": "positive",
      "confidence": 0.97,
      "reason": "The text uses highly positive language ('amazing', 'highly recommended')."
    }
  },
  "meta": {
    "request_id": "demo-002",
    "capability": "sentiment_analysis",
    "elapsed_ms": 612
  }
}
```

---

### 错误示例（未知 capability）

```bash
curl -X POST http://localhost:8000/v1/capabilities/run \
  -H "Content-Type: application/json" \
  -d '{"capability": "unknown", "input": {}}'
```

**失败响应：**

```json
{
  "ok": false,
  "error": {
    "code": "CAPABILITY_NOT_FOUND",
    "message": "Capability 'unknown' is not supported.",
    "details": {"capability": "unknown"}
  },
  "meta": {
    "request_id": "auto-generated-uuid",
    "capability": "unknown",
    "elapsed_ms": 1
  }
}
```

---

## 运行测试

```bash
pytest tests/ -v
```

---

## 项目结构

```
ai-capability-service-youcheng/
├── app/
│   ├── main.py                        # FastAPI 入口
│   ├── router.py                      # 路由：POST /v1/capabilities/run
│   ├── models.py                      # Pydantic 数据模型
│   ├── config.py                      # 环境变量配置
│   ├── exceptions.py                  # 异常类 & 全局 handler
│   ├── logger.py                      # 结构化日志
│   └── capabilities/
│       ├── base.py                    # 抽象基类
│       ├── text_summary.py            # 文本摘要（DeepSeek）
│       └── sentiment_analysis.py     # 情感分析（DeepSeek）
├── tests/
│   └── test_api.py                    # API 测试
├── .env                               # API Key（不提交）
├── .env.example                       # 配置模板
├── requirements.txt
└── README.md
```