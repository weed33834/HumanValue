<p align="center">
  <img src="docs/assets/logo.svg" width="140" alt="HumanValue" />
</p>

<h1 align="center">HumanValue</h1>

<p align="center">
  <strong>Talent Value Intelligence Platform</strong><br/>
  Conversational AI · Agent Tools · Automated Performance Evaluation · Multi-perspective Assessment
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-blue.svg" alt="License" /></a>
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/Node-20+-339933?logo=nodedotjs&logoColor=white" alt="Node 20+" />
  <img src="https://img.shields.io/badge/FastAPI-0.139+-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Vue_3-4FC08D?logo=vuedotjs&logoColor=white" alt="Vue 3" />
  <img src="https://img.shields.io/badge/LangGraph-agent-FF6B6B" alt="LangGraph" />
  <a href="CHANGELOG.md"><img src="https://img.shields.io/badge/version-1.0.1-blue.svg" alt="Version 1.0.1" /></a>
</p>

<p align="center">
  <strong>Read this in:</strong> <a href="README.md">English</a> · <a href="README.zh-CN.md">中文</a> · <a href="README.ja-JP.md">日本語</a>
</p>

<p align="center">
  <img src="docs/assets/demo/humanvalue-promo.gif" width="640" alt="HumanValue Demo" />
</p>

---

**HumanValue** is an AI-driven platform that quantifies and grows talent value. It combines a conversational AI agent, a full agent toolchain, and automated multi-perspective evaluation — designed for managers and HR to understand, develop, and maximize the value of every person. The UI is **English-first** with switchable **中文 / 日本語**.

---

## Highlights

- **Conversational AI & Agent Console** — an AI assistant that is also a control console: run analyses, create announcements, manage tickets, run pipelines, take backups, and more, directly in chat.
- **Talent Value Engine** — 10 theory-driven analyses: 9-box classification, key-person / single-point-of-failure risk, Pareto concentration, team efficiency, incentive strategy, compensation competitiveness, succession pipeline, burnout warning, skill-fit & reallocation, and quarterly review.
- **Multi-System-Type** — the same engine adapts to different institutional contexts: enterprise (elimination-based), academia (cultivation-based), public sector (promotion-based), training (certification-based), and gig platforms (flexible).
- **Enterprise Governance** — MFA, login brute-force protection, announcements, tickets, data assets, data pipelines, disaster recovery backups, and AI security red-team.
- **Universal Agent Capabilities** — ReAct loop, planner, reflector, multi-agent supervisor, MCP client/server, A2A protocol, browser automation, skills, memory & RAG, streaming SSE, context compression, and more.

## Product Preview

| Talent Dashboard | Talent Value Engine | AI Assistant (Chat Console) |
|:---:|:---:|:---:|
| ![Talent Dashboard](docs/assets/demo/02-dashboard.png) | ![Talent Value](docs/assets/demo/04-talent-value.png) | ![AI Assistant](docs/assets/demo/05-chat-complex.png) |

| Command Palette | Create Announcement (via Chat) | Dark Mode |
|:---:|:---:|:---:|
| ![Command Palette](docs/assets/demo/03-command-palette.png) | ![Console Announcement](docs/assets/demo/06-console-announcement.png) | ![Dark Mode](docs/assets/demo/09-dark.png) |

> See the full walkthrough in the [Demo Showcase](docs/demo-showcase.md).

## Architecture

- **Frontend**: Vue 3 · Pinia · Element Plus · ECharts · KaTeX · Mermaid
- **Backend**: Python 3.11+ · FastAPI · SQLAlchemy · Alembic
- **Agent**: LangGraph · ReAct · LangChain tools · MCP · A2A
- **LLM Providers**: OpenAI / Anthropic / Gemini / DeepSeek / Qwen / Ollama (encrypted credentials, load-balanced)
- **Storage**: SQLite (dev) / PostgreSQL (prod) · ChromaDB · Redis · MinIO
- **Observability**: Prometheus · Langfuse · Grafana · Loki

## Quick Start

### Docker Compose (recommended)

```bash
git clone https://github.com/weed33834/HumanValue.git
cd HumanValue
cp backend/.env.example backend/.env   # set JWT_SECRET_KEY and a model API key
docker compose up -d --build
```

### Local Development

```bash
# backend
cd backend && pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# frontend
cd frontend && npm install && npm run dev   # http://localhost:5173
```

### No API Key? Mock Mode

```bash
cd backend && uvicorn main:app --reload --port 8000
python -m eval.evaluate --mock
```
When no LLM API key is configured, the system falls back to a deterministic Mock Provider so the full pipeline runs end-to-end.

## Demo

See the [Demo Showcase](docs/demo-showcase.md) for the complete recorded walkthrough, screenshots, and the promotional GIF.

## Documentation

| Document | Description |
|---|---|
| [Demo Showcase](docs/demo-showcase.md) | Recorded video + screenshots |
| [Universal Agent Capabilities](docs/universal-agent.md) | Full universal agent feature checklist |
| [Talent Value Engine](docs/m14-m18-capabilities.md) | Capabilities & APIs |
| [Chat Console Guide](docs/chat-console.md) | How to operate the app via conversation |
| [Shortcuts & Tips](docs/shortcuts.md) | Global shortcuts & usage tips |
| [Error Codes](docs/error-codes.md) | Unified error code handbook |
| [Agent Pitfalls](docs/agent-pitfalls.md) | Common pitfalls & regression gates |
| [Launch Checklist](docs/launch-checklist.md) | Pre-release verification |
| [Changelog](CHANGELOG.md) | Version history |

## Repositories

| Platform | URL |
|---|---|
| GitHub (primary) | https://github.com/weed33834/HumanValue |
| GitCode (mirror) | https://gitcode.com/badhope/HumanValue |
| Gitee (mirror) | https://gitee.com/badhope/HumanValue |

## License

Apache License 2.0. See [LICENSE](LICENSE).
