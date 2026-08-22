# AGENTS.md — HumanValue 工程协作规范

> 本文件是 AI 协作者与人类贡献者在 HumanValue 仓库中的唯一规则源。
> 硬约束共 10 条（§6），全部 P0；其余为工作流说明。

## 1. 项目定位

HumanValue 是面向企业与高校的人才价值智能平台：对话式 AI 助手 + Agent 工具链 +
自动化多视角人才评估（九宫格、继任、倦怠预警等 10 类分析）。

## 2. 技术栈与版本口径

| 维度 | 口径 |
|---|---|
| Python 运行时下限 | **3.11+**（README 徽章为准） |
| CI 验证版本 | 3.12 |
| ruff `target-version` | `py310` — 仅是语法解析下限，不代表运行时支持下限，勿混淆 |
| Node | 20+（前端构建 / TS SDK） |

后端 FastAPI + SQLAlchemy + Alembic；前端 Vue 3 + Pinia + Element Plus；
Agent 层 LangGraph/LangChain；存储 SQLite(开发)/PostgreSQL(生产) + ChromaDB + Redis。

## 3. 平台拓扑

- **GitHub（主仓库）**: https://github.com/weed33834/HumanValue — 开发、Issue/PR、CI 全部在此。
- GitCode / Gitee: 发布镜像，由同步流程更新，不直接在上面开发。

## 4. 仓库布局

```
backend/    FastAPI 后端（api/ agent/ auth/ core/ services/ models/ tests/ alembic/）
frontend/   Vue 3 前端
sdk/        python(humanvalue 包) 与 typescript(@humanvalue/sdk) 开放 API SDK
deploy/k8s  K8s 清单; docker-compose(.prod).yml 为容器编排入口
monitoring/ Prometheus 告警规则; grafana/ 看板与 provisioning
docs/       产品/部署/合规文档; scripts/ 根级工具脚本
```

## 5. 常用命令

```bash
# 后端
cd backend && pip install -r requirements.txt
uvicorn main:app --reload --port 8000
python -m pytest -x -q                 # 测试（约 1850 例）
ruff check . && black --check .        # lint（CI 同款版本见 ci.yml）

# 前端
cd frontend && npm install
npm run dev                            # http://localhost:5173
npm run lint && npm test && npm run build

# 版本发布
# 见 §7 版本策略；四处同步点必须一起改
```

## 6. 安全红线（P0，违反即回滚）

1. 密钥只走环境变量/`.env`；源码、文档、日志中禁止出现任何真实 token/password/连接串。
2. `.env` 永不入库（已在 .gitignore）；示例一律放 `.env.example` 且值用占位符。
3. 生产守护：`HUMANVALUE_ENV=production` 时 demo 认证被强制关闭、占位 JWT_SECRET_KEY 被
   `scripts/check_prod_readiness.py` 拦截——不得绕过或削弱该链路。
4. 不编造事实/API/库；不确定先查证或在回复中显式标注"推测"。
5. 关键信息缺失或操作具有破坏性（force push、删远程分支、改可见性）时，先澄清再动手。
6. 最小变更：只改任务要求的文件；发现顺手可优化处列为"⚠️ 待办建议"，不顺手改。
7. 失败熔断：同一 Bug 连续修复失败 2 次、终端命令连续失败 3 次，停止盲试，
   输出故障报告（现象/已试方案/疑似根因）并请求人工介入。
8. 提交前必跑 `git status` + `git diff`，确认无冗余文件与敏感信息混入。
9. 大文件（>100 行）重写前先提醒 `git commit` 或自行备份；优先函数级精确替换。
10. Windows/PowerShell 环境：用 `Remove-Item` 而非 `rm`、`$env:VAR` 而非 `export VAR`；
    文本读写注意 UTF-8（PS 5.1 的 `Set-Content` 默认 ANSI 会损坏中文）。

## 7. 版本策略

- `VERSION` 文件是唯一权威版本号，当前语义化版本自 **v1.0.0** 起。
- 每次对外可见的变更递增尾数补丁号，且必须同步以下四处：
  1. `VERSION`
  2. `frontend/package.json` 的 `version`
  3. 三语 README 徽章 `badge/version-X.Y.Z-blue.svg`
  4. `CHANGELOG.md` 顶部新增条目
- 内部纯重构若无行为变化，也按补丁号递增并在 CHANGELOG 注明。

## 8. Git 工作流

- 主干 `main` 受保护：一切变更经 PR → CI 全绿 → squash 合入。
- 分支命名 `fix/* feat/* docs/*`；提交信息遵循 Conventional Commits（中文描述），主题行注明目标版本号。
- CI 约 20 分钟（Backend Tests 是大头）；合并前等待全部检查完成。
- `git push -f` 仅限用户明确批准的历史重建场景。
- PR 描述需含：变更内容、风险说明（尤其 Redis 键前缀/env 变量名等升级不兼容项）、验证方式。

## 9. 文档索引

| 文档 | 内容 |
|---|---|
| README.zh-CN.md | 产品总览与快速开始 |
| CHANGELOG.md | 版本历史（Keep a Changelog 格式） |
| docs/deployment-guide.md | 部署指南 |
| docs/alerting-rules.md | 监控告警指标清单（humanvalue_* 指标） |
| docs/error-codes.md | 统一错误码 |
| docs/pilot-runbook.md | 试点上线手册 |

## 10. 质量基线与爬坡路线（2026-08-22 审计后确立）

- 实测覆盖率 **60.94%**（59,747 语句），CI 门禁已提至 `--cov-fail-under=60`。
- 目标 70%：只允许随真实测试逐 PR 爬坡（门禁跟随实测值上调），
  禁止用降低断言强度/跳过用例的方式凑数——那是另一种虚假实现。
- 缺口集中区：agent 工具链（editor/file_tools/git_integration 等 0-8%）、
  graph_rag/hybrid_search 服务、api/routes.py 主路由。补测优先选纯逻辑模块。
- ruff 已强制 F401/F841/F541（v1.0.9 归零）；E741/F402 暂豁免，专项治理后启用。
