# 上线就绪检查清单（HumanValue Launch Checklist）

> 目标：发布/落地前逐项验证，杜绝"上线才发现"的问题。配合 `make check-backend` 质量门禁使用。

## 一、构建与质量（CI 卡点）
- [ ] 后端质量门禁通过：`cd backend && python scripts/check_backend_quality.py`（语法 / 路由签名 / 依赖 / 字段密钥）
- [ ] 后端单测通过：`python -m pytest -x -q`（1500+ 用例）
- [ ] 前端构建通过：`cd frontend && npm run build`
- [ ] 前端 ESLint / Prettier：`npm run lint && npm run format:check`
- [ ] Docker Compose 校验：`docker compose config -q`

## 二、配置与密钥
- [ ] `JWT_SECRET_KEY`：至少 32 字符强随机，`AGENTVALUE_ENV=production`
- [ ] `FIELD_ENCRYPTION_KEY`：32 字节（44 字符 base64 或 64 字符 hex），`python -c "import base64,os;print(base64.b64encode(os.urandom(32)).decode())"`
- [ ] `CORS_ORIGINS`：设置为实际前端域名
- [ ] `DATABASE_URL`：切换到 PostgreSQL
- [ ] `REDIS_URL`：配置用于限流 / 队列 / 缓存
- [ ] LLM 凭据：`CLOUD_API_KEY` + `CLOUD_BASE_URL`，或在管理端配置供应商
- [ ] `LLM_CACHE_ENABLED`：生产可按需开启（建议压测回归后开）
- [ ] 登录风控：`LOGIN_LOCK_THRESHOLD` / `MFA_ENFORCE_ADMIN`（建议强制管理员 MFA）
- [ ] 容灾：`BACKUP_DIR` 挂载持久卷，`DR_RTO/RPO_TARGET_SECONDS` 按 SLA 设置

## 三、功能冒烟（上线前手动走一遍）
- [ ] 登录 / 注册 / MFA 绑定与登录 / 忘记密码
- [ ] 多模型对话（多轮、工具调用、联网搜索、语音输入、文件上传）
- [ ] 评估流程：录入 → AI 评估 → 管理者审批 → HR 审计 → 员工通知 / 申诉
- [ ] 看板：管理者 / HR / 员工 / 管理员各角色数据正确
- [ ] 企业治理：公告、工单、登录风控、数据资产、容灾备份恢复
- [ ] 管理端：模型 / 供应商 / 提示词 / 知识库 / 安全红队 / 数据管道

## 四、安全与合规
- [ ] 所有用户可见报错为"人话 + 错误码 + 文档链接"（三段式）
- [ ] 敏感字段已加密（FIELD_ENCRYPTION_KEY 生效日志确认）
- [ ] 审计日志哈希链可校验（`/audit-logs/verify-chain`）
- [ ] 越权访问被 RBAC / ABAC 拦截（用非管理员账号验证）
- [ ] HTTPS 全链路（反向代理 TLS 终止）
- [ ] 演示模式关闭：`AUTH_DEMO_MODE=false`，前端 `isDemoAuthEnabled()=false`

## 五、性能与可靠性
- [ ] 流式空闲超时已配置（`LLM_STREAM_IDLE_TIMEOUT`），上游慢/挂时不会无限阻塞
- [ ] 上游 Provider 降级链可用（多档位 fallback）
- [ ] 数据库备份可恢复演练通过（DR 演练 `passed`）
- [ ] 监控：Prometheus 指标 `/metrics`、健康检查 `/health`、审计日志可查

## 六、文档
- [ ] [快捷键与使用技巧](shortcuts.md)
- [ ] [智能体陷阱与防护](agent-pitfalls.md)
- [ ] [错误码手册](error-codes.md)
- [ ] [完整版能力说明](m14-m18-capabilities.md)
- [ ] README（中/英/日）与实际功能一致

## 上线后首日观察
- [ ] 错误率 / 延迟 / 成本看板正常
- [ ] 首 token 延迟（TTFT）达标
- [ ] 告警通道（邮件/Webhook）可达
