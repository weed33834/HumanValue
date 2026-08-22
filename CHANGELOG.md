# Changelog

本文件记录 HumanValue 所有显著变更,格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/),
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [v1.0.2] - 2026-08-22

### 品牌残留全量清理 (AgentValue → HumanValue)

- 全库 85 个文件完成品牌统一,大小写三形态(AGENTVALUE/AgentValue/agentvalue)零残留:
  - **运行时标识**: 环境变量 `AGENTVALUE_ENV` → `HUMANVALUE_ENV`; Settings 字段 `agentvalue_env` → `humanvalue_env`
  - **可观测性**: Prometheus 指标前缀 `agentvalue_*` → `humanvalue_*`(25 个指标),同步更新 grafana/dashboard.json、monitoring 告警规则与 docs/alerting-rules.md
  - **内部键空间**: Redis key 前缀 `agentvalue:*` → `humanvalue:*`(job/rate_limit/dead_letter); OTEL 默认服务名 → `humanvalue-backend`
  - **KMS/Vault 默认路径**: `alias/agentvalue-field-kek`、`agentvalue/jwt-signing-key` 等 → humanvalue 前缀
  - **演示默认密码**: `agentvalue123` → `humanvalue123`
- **Python SDK 包改名**: `sdk/python/agentvalue/` → `sdk/python/humanvalue/`,pyproject 包名同步
- **TypeScript SDK 改名**: `@agentvalue/sdk` → `@humanvalue/sdk`(package.json + package-lock)
- k8s 清单、docker-compose、前后端页面文案、设计文档全部对齐;镜像命名 humanvalue-backend/frontend 与 CI 构建一致
- 验证: 大小写不敏感 grep 零命中; python compileall 通过; ruff/black 本地全绿

## [v1.0.1] - 2026-08-22

### 平台定位更正

- **主仓库更正**: GitHub (`weed33834/HumanValue`) 为唯一主仓库,承担开发、Issue/PR 与 CI; GitCode 与 Gitee 为发布镜像。
- 三语 README 的"仓库"表格与快速开始克隆地址同步更正,消除文档与实际平台策略相反的问题。

## [v1.0.0] - 2026-08-22

### 历史重建基线

- **版本号重置**: 项目以 v1.0.0 作为公开版本的起点。此前的内部迭代记录(v2.x 系列)已随仓库历史一并归档,不再保留。
- **单一版本源**: `VERSION` 文件为唯一权威版本号; `frontend/package.json` 与三语 README 徽章必须与之同步。
- **历史重建**: 开源前所有提交压缩为单个基线提交,旧历史不再对外呈现。
- 后续变更自 v1.0.1 起,按语义化版本递增尾数补丁号。

[v1.0.0]: https://github.com/weed33834/HumanValue/releases/tag/v1.0.0
