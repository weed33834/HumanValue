# 智能体常见陷阱与防护（HumanValue 实践）

> 目的：把开发/测试中反复出现的问题与智能体搭建的常见坑**固化为防复发机制**，
> 避免"下次再说这种问题"。

## 一、本仓库出现过的问题与根治

| 问题 | 根因 | 根治 / 防复发 |
|---|---|---|
| **路由 `request` 被误判为查询参数 → 422** | FastAPI 处理函数 `request` 参数缺 `Request` 类型注解，且 `from __future__ import annotations` 使注解延迟求值，FastAPI 无法识别为特殊参数 | 1. 全部修复（含 api/routes、public/v1_routes、experiment_routes 等既有文件）<br>2. `scripts/check_backend_quality.py` 用 AST 扫描所有处理函数，`request` 参数必须带 `: Request` 且 fastapi 已导入，否则 CI 失败 |
| **`@rate_limit` 处理函数缺 request/response → 导入即崩** | slowapi 的 limiter 要求函数签名含 request/response | 质量门禁 AST 检查所有 `@rate_limit` 处理函数 |
| **笛卡尔积查询** | `provider_resolver` 租户凭据查找表间缺连接条件 | 改为显式按活跃凭据 id 关联；门禁+测试覆盖 |
| **聊天可无限阻塞** | 流式无空闲超时，上游慢/挂时挂死 | 新增 `llm_stream_idle_timeout`(默认90s) + `_anext_with_idle_timeout` 包装；超时抛 ProviderError → SSE error 事件 |
| **FIELD_ENCRYPTION_KEY 非法** | 密钥非 32 字节（需 44 base64 / 64 hex） | 质量门禁校验；`field_crypto` 启动时明确告警 |
| **可选依赖缺失导致功能 501** | pyotp/playwright 等未装 | 全部写入 requirements.txt（可选段）；门禁扫描并告警对应降级功能 |
| **批量 sed 破坏多行 import** | 自动化文本替换不识别括号式 import | 门禁 `py_compile` 全量编译，任何语法错误即 CI 失败 |
| **沙箱重置丢工作** | 环境非持久 | 策略：每次变更后立即 commit + push 到三个远端（gitcode/github/gitee），仓库始终有最新副本 |

## 二、智能体搭建常见坑（对照检查）

### 1. 多轮上下文丢失
- **坑**：第二轮回不会引用第一轮，或上下文被截断。
- **HumanValue**：`session_prompt` 从 DB 组装完整消息历史（含工具结果标注 `[工具调用结果]`），验证第二轮回正确引用第一轮结果。

### 2. 工具调用失效 / 格式不兼容
- **坑**：不同模型工具调用返回格式不同；工具结果未回喂。
- **HumanValue**：`ToolRegistry.resolve_schemas` 统一 OpenAI function schema；工具结果以 user 消息回喂；实测计算器 `25*4=100`。

### 3. 上游 Provider 降级
- **坑**：某个模型/通道挂掉导致整体不可用或无限挂起。
- **HumanValue**：`model_router` 多档位 fallback + 流式空闲超时；上游连接失败时返回 `provider-error` SSE 事件（不崩溃、不挂死）。

### 4. 提示注入 / 越狱
- **坑**：用户输入覆盖系统指令、恶意工具调用。
- **HumanValue**：`InputGuard` + `OutputGuard`（注入/越狱/PII 脱敏）+ 红队演练台实测检测率。

### 5. 暴力破解 / 安全
- **坑**：无登录风控。
- **HumanValue**：登录风控（邮箱/IP 锁定）+ MFA 双因子 + 管理员解锁。

### 6. 结构化输出解析失败
- **坑**：LLM 输出带 markdown 包裹/多 JSON 块，解析直接抛异常。
- **HumanValue**：`safe_json_parse` 容错解析 + `OutputValidator` JSON Schema 校验 + 错误码 `E-VALID-3002`。

### 7. 密钥 / 凭据
- **坑**：凭据明文落库、密钥长度不对。
- **HumanValue**：`field_crypto` AES-GCM 加密存储 + KMS 可选；质量门禁校验密钥长度。

### 8. 并发 / 超时
- **坑**：请求无超时、无限流。
- **HumanValue**：slowapi 限流 + `llm_request_timeout` + 流式空闲超时 + 全局异常处理。

## 三、防复发机制（一键自检 + CI 卡点）

```bash
# 本地一键自检（语法/路由签名/依赖/密钥）
cd backend && python scripts/check_backend_quality.py
# 或
make check-backend
```

- **CI**：`.github/workflows/ci.yml` 的 Backend Lint 任务已加入质量门禁，任何上述问题都会让 PR/合并失败。
- **Makefile**：`lint-backend` 与 `check-backend` 目标已含门禁。

> 原则：**问题发生后 → 定位根因 → 修复 → 写进门禁/测试 → 以后自动拦截，不再"下次再说"。**
