# Changelog

本文件记录 HumanValue 所有显著变更,格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/),
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [v1.0.9] - 2026-08-22

### 全量审计第四批: 质量门禁爬坡 (覆盖率 60% + ruff 规则强制化)

- **覆盖率门禁 50% → 60%**: 实测基线 60.94%(59,747 语句,1877 用例)。
  70% 目标确立为逐 PR 爬坡路线(见 AGENTS.md §10),
  明确禁止用弱化断言方式凑数。
- **ruff F401 强制化**: 42 处未使用导入全量清理(28 文件,tests 零涉及,
  无副作用导入风险),从 ignore 列表移除转为 CI 门禁。
- **ruff F841 强制化**: 7 处未使用变量逐个人工裁定修复,其中发现并修复
  hybrid_search_service 3 处日志 f-string 缺前缀导致异常信息从未被打印的连带 bug;
  E741(15 处)/F402 暂保留豁免并注明治理计划。
- **ruff F541 强制化**: 4 处无占位符 f-string 清理。

## [v1.0.8] - 2026-08-22

### 全量审计第三批: 重复造轮子收口 (JSON 解析 / ISO 时间解析)

**JSON 容错解析 ×4 收口为唯一实现 `core/json_utils.py`**(此前 agent/_json_util、
agent/multi_agent、agent/skills、services/graph_rag_service 各持一份拷贝,
失败语义分裂且部分已退化):

- 新增权威 API: `find_json_object`(失败返回 None,合法 `{}` 可区分) +
  `safe_json_dict`(失败返回 {},兼容历史语义) + `call_llm_json/call_llm_text`
- 补齐历史实现缺失的单行代码围栏(`` ```json {...} ``` ``)支持
- `agent/_json_util.py` 改为薄委托,旧导入路径保持有效;
  multi_agent 删除逐字拷贝的 `_safe_json_parse/_call_llm_json`
- skills `_extract_json`、graph_rag `_extract_json_block/_safe_json_loads`
  改为委托;llm_judge(两处)的裸 `json.loads` 升级为容错解析,
  解析失败时的正则兜底路径保持不变

**ISO 时间解析 ×3 收口至 `api/admin/_common.parse_iso_datetime`**
(api_health/analytics_v2/trace_v2 三份逐字拷贝删除);
保留 Z/z 后缀兼容,新增 default= 参数支持失败返回默认值。
billing_routes 的变体契约(Optional/无时区归一)经判定语义不同,保留并文档化。

**判定保留的非问题**: SSE 缓冲(单实现)、rate_limit 双层设计(刻意分层)、
JWT/密码/邮箱(正确使用库)、数据集生成器双版本(文档化的有意分叉)。

新增 36 个专项测试(test_json_utils/test_admin_common)。

## [v1.0.7] - 2026-08-22

### 全量审计第二批: 基础设施一致性与告警链路修复

- **告警通知链路修复(此前开箱即坏)**: critical-webhook 原指向 Alertmanager 自身端口形成无效回环;
  现改由 `ALERT_WEBHOOK_URL` 环境变量注入,compose 启用 `--config.expand-env`,
  未配置时兜底 `.invalid` 域名——投递失败留日志可发现,而非静默假成功;
  移除文件头关于"SMTP 凭据经 entrypoint 注入"的不实注释。
- **品牌残留新变体清理**: 告警名 `Empvalue*` → `Humanvalue*`(alerts.yml / alertmanager.yml /
  docs/alerting-rules.md,此大小写形态逃过了此前的三形态扫描)。
- **k8s 模板占位密钥防线**: secret.yaml 的模板占位值(JWT/FIELD_ENCRYPTION_KEY)加入
  check_prod_readiness 黑名单,新增回归测试锁定——模板原样 apply 到生产不再误报 PASS。
- **release 版本守卫**: tag 必须与 VERSION 文件一致才能走发布链,杜绝 v9.9.9 式漂移发布。
- **security.yml**: 删除假 `--ignore-vuln GHSA-xxxx-ignore-placeholder` 占位 ID,
  改为正确解析 pip-audit-ignore.txt(过滤注释行并逐条转 --ignore-vuln 参数)。
- **dependabot.yml**: 移除 schema 不支持的 `auto-merge` 无效键(自动合并由专用 workflow 负责)。
- **杂项一致性**: waf-ingress.yaml 引用不存在的 waf-configmap.yaml 已更正;
  grafana provisioning 文件 agentvalue.yml 改名 humanvalue.yml 并修正注释中的过期文件名。

## [v1.0.6] - 2026-08-22

### 全量审计第一批: 虚假实现与弱实现修复

对全部 456 个后端文件 / 132 个前端文件 / SDK / 脚本 / 部署清单完成虚假实现扫描,
本批修复确认的问题(合法降级器如 MockProvider/DummyIMAdapter 经裁定保留):

- **kb_sync_service**: S3/Database/Git 数据源此前静默返回空列表并记 success;
  现显式抛错并落 failed 状态,不再伪装成功同步
- **admin/debug**: 7 个 trace span 时长为启发式估算,现统一打 `estimated` 标记
  并在 timeline 增加 `durations_estimated`; 移除 hardware_report 的死 try/except
- **engagement_routes**: 删除拼写错误路由 `/recognizations`(零引用零测试)
- **calibration_routes**: 删除 `item.calibrated_score` 裸表达式死代码
- **e2e_smoke**: `/metrics` 断言因运算符优先级恒真,修复为同时校验状态码与指标内容
- **analytics_service_v2**: 按天分组由 SQLite 方言 strftime 改为跨方言 func.date,
  修复 PostgreSQL 下聚合报错的隐患
- **openai_provider**: 流式重试与通用 `_retry` 统一使用 MAX_RETRIES 与 RateLimitError
  类型判定;删除 anthropic/gemini provider 未使用的 `_MAX_RETRIES` 死常量
- **db_backup**: 恢复验证失败现写入 critical 告警并尝试外发通知(原为 TODO 仅记日志)
- **llm_judge**: 文档如实声明能力边界——被评对象固定由 MockProvider 生成,
  不构成对真实 LLM 的端到端评测
- **run_fairness_monthly / sla_monitor**: 合成数据月报现在显著标注 SYNTHETIC 横幅,
  新增 `--input` 支持传入真实记录;避免造数报告被误读为真实审计结论
- **前端 mobile 路由**: PlaceholderView 此前为零引用孤儿组件,现挂载为 `/m/*`
  兜底引导页(深链未适配页面时提供桌面端等价路径跳转),配套测试保留有效
- **sdk/python**: 移除指向不存在 tests 目录的 pytest 配置

## [v1.0.5] - 2026-08-22

### 自动化: 镜像同步 + 版本一致性门禁

- **新增 `sync-mirrors` workflow**: main 更新后自动强制同步到 GitCode/Gitee 镜像;
  Secrets `GITCODE_KEY`/`GITEE_TOKEN` 未配置时跳过对应目标,不阻塞流水线。
- **新增版本一致性门禁**: `scripts/check_version_consistency.py` 校验 VERSION /
  package.json / 三语 README 徽章 / CHANGELOG 顶部条目五处一致,已接入 ci.yml 首个检查步。
  此前 VERSION=2.8.0、徽章=2.8.1、CHANGELOG=2.8.5 三处漂移的问题从此被 CI 拦截。

## [v1.0.4] - 2026-08-22

### 产品落地: 企业/高校方案 + 员工权利合规

- **新增 `docs/adoption-enterprise-academia.md`**: 企业与高校双场景画像(体系类型映射)、
  角色功能地图、P0-P3 分阶段落地路线、集成清单(SSO/飞书/GitLab/本地大模型)、KPI 与常见坑。
- **新增 `docs/compliance-employee-rights.md`**: PIPL 第24条 / GDPR 第22条 / EU AI Act
  自动化决策合规指引;盘点平台内置合规能力(审批流人工复核、RBAC/ABAC、字段加密、
  数据保留、审计日志、公平性审计、GDPR 审计);部署方 Go-Live 义务清单与反模式。
- 三语 README 文档表新增两篇链接。
- 定位澄清: 平台以"辅助决策"姿态服务企业与高校,处置类结论必须经人工审批闭环。

## [v1.0.3] - 2026-08-22

### CI 加固与协作规范重写

- **Dependabot 自动合并收紧**: 仅允许 semver-patch 自动合并(minor 一律人工审查);
  移除"无检查直接合并"路径——检查尚未注册时一律等待,超时则放弃合并而非盲合。
- **AGENTS.md 重写**: 由 602 行通用 AI 治理模板精简为项目专属工程规范(10 条 P0 红线),
  移除对不存在文件(PROJECT.md/sync_rules.py)与外部规则仓库(/workspace/AI-rule、AI-RULE.git)的引用。
- **Python 版本口径统一**: 明确运行时下限 3.11+(README/AGENTS.md)、CI 验证 3.12、
  ruff target py310 仅为语法解析下限并在 pyproject 注释澄清,消除四处口径冲突。

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

[v1.0.7]: https://github.com/weed33834/HumanValue/releases/tag/v1.0.7
[v1.0.6]: https://github.com/weed33834/HumanValue/releases/tag/v1.0.6
[v1.0.5]: https://github.com/weed33834/HumanValue/releases/tag/v1.0.5
[v1.0.4]: https://github.com/weed33834/HumanValue/releases/tag/v1.0.4
[v1.0.3]: https://github.com/weed33834/HumanValue/releases/tag/v1.0.3
[v1.0.2]: https://github.com/weed33834/HumanValue/releases/tag/v1.0.2
[v1.0.1]: https://github.com/weed33834/HumanValue/releases/tag/v1.0.1
[v1.0.0]: https://github.com/weed33834/HumanValue/releases/tag/v1.0.0
