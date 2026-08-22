# HumanValue — 完整版能力补齐说明 (M0-M29)

对照 agent-builder-skill 完整版清单 (M0-M29) 补齐的能力，覆盖 **Agent 高级能力**、
**企业级治理 (M14)**、**底层基础 (M18)**、**错误码 (M19)**、**数据治理 (M20)**、
**性能缓存 (M23)**、**AI 安全 (M25)**、**数据管道 (M28)**、**容灾 (M29)**。

> 所有能力均为真实后端实现（模型 + 服务 + 路由 + 测试），非空壳。

---

## 1. Agent 高级能力 (M3/M4/M6/M12)

### Planner 规划器 (M3.8) — `backend/agent/planner.py`
Plan-and-Execute：任务拆解为步骤 → 逐步执行 → 中途 replan。

```bash
POST /api/v1/admin/agent-advanced/planner/run   # 规划+执行闭环
POST /api/v1/admin/agent-advanced/planner/plan  # 仅规划
```

### Reflector 反思器 (M3.9) — `backend/agent/reflector.py`
Evaluator-Optimizer：生成 → LLM-as-judge 评审 → 不达标带反馈重生成。

```bash
POST /api/v1/admin/agent-advanced/reflector/run
```

### MCP Server (M4.17) — `backend/agent/mcp_server.py`
把 agent 工具暴露为 MCP 服务器（内置轻量 JSON-RPC + 可选 FastMCP）。

```bash
GET  /api/v1/admin/agent-advanced/mcp-server
POST /api/v1/admin/agent-advanced/mcp-server/call
```

### A2A 协议 (M6.15/16) — `backend/agent/a2a_client.py` / `a2a_server.py`
跨智能体通信。Agent Card + JSON-RPC。

```bash
GET  /.well-known/agent.json
POST /a2a   # tasks/send | tasks/get | tasks/cancel | tasks/list
```

### Browser 浏览器自动化 (M4.8) — `backend/agent/browser_tool.py`
Playwright 工具，已接入 ToolRegistry。

---

## 2. 企业级治理 (M14, 16-enterprise-org.md)

### MFA 双因子 (C.3)
```bash
POST /api/v1/auth/mfa/enroll   # 绑定 (返回 secret + otpauth URI)
POST /api/v1/auth/mfa/verify   # 验证并启用
POST /api/v1/auth/mfa/disable
GET  /api/v1/auth/mfa/status
# 登录时已绑定 MFA 需携带 otp
```

### 登录风控 (C.6/C.8)
```bash
GET  /api/v1/admin/enterprise/login-attempts
GET  /api/v1/admin/enterprise/login-lockouts
POST /api/v1/admin/enterprise/unlock
```

### 公告 (K.3) / 工单 (K.13)
```bash
# 用户侧
GET  /api/v1/announcements · /announcements/unread-count · POST /announcements/{id}/read
POST /api/v1/tickets · GET /tickets/me · POST /tickets/{id}/comments
# 管理侧
GET/POST /api/v1/admin/enterprise/announcements
GET /api/v1/admin/enterprise/tickets · PUT .../status · POST .../assign
```

---

## 3. 底层基础 (M18, 20-foundation-capabilities.md)

### 文本处理 — `backend/core/text_utils.py`
关键词提取 (TF-IDF + TextRank)、归一化、摘要、去重。

```bash
POST /api/v1/text/keywords · /summarize · /dedup · /normalize · /fingerprint
```

### 结构化输出校验 — `backend/core/output_validator.py`
```bash
POST /api/v1/text/validate-schema
```

### 错误码体系 (M19) — `backend/core/errors.py` + `docs/error-codes.md`
```bash
GET /api/v1/text/error-codes
```

---

## 4. 数据治理 (M20, 22-data-governance.md)
`models/data_asset.py` + `services/data_governance_service.py`：资产登记/搜索/分类分级/血缘/质量/使用统计。

```bash
GET/POST /api/v1/admin/data-governance/assets · .../summary · .../{id}/lineage · .../{id}/usage
```

---

## 5. 性能缓存 (M23, 25-performance-engineering.md)
`backend/core/llm_cache.py`：精确哈希 + 可选语义缓存，集成进 `core/llm_call.py`。

```bash
GET  /api/v1/admin/llm-cache/stats · POST /clear · GET /config
```
配置：`LLM_CACHE_ENABLED` / `LLM_CACHE_TTL` / `LLM_CACHE_MAX_SIZE`

---

## 6. AI 安全攻防与红队 (M25, 27-ai-security.md)
威胁用例库 / 安全事件中心 / 红队演练台（联动现有 InputGuard）。

```bash
POST /api/v1/admin/security/threat-cases/seed · GET/POST .../threat-cases
POST /api/v1/admin/security/redteam/run · GET .../redteam/runs
GET  /api/v1/admin/security/events · POST .../events/{id}/dispose
GET  /api/v1/admin/security/overview
```

---

## 7. 数据管道与集成 (M28, 30-data-pipeline.md)
数据源 / 管道 / 转换规则 / 质量 / 同步统计。

```bash
POST /api/v1/admin/pipeline/sources · .../{id}/test
POST /api/v1/admin/pipeline/transform-rules · .../{id}/test
POST /api/v1/admin/pipeline/pipelines · .../{id}/run
GET  /api/v1/admin/pipeline/stats · .../records
```

---

## 8. 容灾与业务连续性 (M29, 31-disaster-recovery.md)
备份 / 恢复 / DR 计划 / 演练 / 连续性指标。

```bash
POST /api/v1/admin/dr/backups · .../{id}/verify · .../{id}/restore
POST /api/v1/admin/dr/plans · .../{id}/publish
POST /api/v1/admin/dr/drills · .../{id}/run
GET  /api/v1/admin/dr/metrics
```
配置：`BACKUP_DIR` / `DR_RTO_TARGET_SECONDS` / `DR_RPO_TARGET_SECONDS`

---

## 9. 测试

```bash
cd backend
python -m pytest tests/test_agent_advanced.py -q
python -m pytest tests/test_enterprise_governance.py -q
python -m pytest tests/test_text_processing.py -q
python -m pytest tests/test_data_governance.py -q
python -m pytest tests/test_disaster_recovery.py -q
python -m pytest tests/test_pipeline.py -q
python -m pytest tests/test_security.py -q
```
