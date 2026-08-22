# 通用智能体能力清单（Universal Agent Capabilities）

> HumanValue 已具备通用智能体的**全部核心能力**，并叠加了人才价值分析、企业治理等垂直能力。
> 本清单逐项核对（均为真实实现，可运行验证）。

## 一、对话与交互
| 能力 | 说明 |
|---|---|
| 多轮对话 | 会话持久化，多轮上下文正常引用 |
| 流式输出 (SSE) | 逐 token 渲染，支持中断/停止 |
| 上下文压缩 | token 预算折叠，长对话不超窗口 |
| 联网搜索 | web_search 实时检索 |
| 网页抓取 | web_fetch 正文提取 |
| 语音输入 (STT) | 浏览器原生 + 文件降级 |
| 文件上传/多模态 | 图片可被多模态模型理解 |

## 二、工具系统
| 能力 | 说明 |
|---|---|
| 工具注册/解析 | ToolRegistry + OpenAI function schema |
| 计算器/日期/数学 | 内置工具 |
| Bash/Shell | 30s 超时 + 截断 |
| 文件读/写/编辑/搜索 | read/write/edit/glob/grep |
| 代码解释器 | 受限沙箱执行 Python |
| 浏览器自动化 | Playwright 导航/点击/截图 |
| MCP 客户端/服务器 | 接入/暴露 MCP 工具 |
| 对话控制台工具 (16) | 对话内调用业务服务 |

## 三、智能体范式
| 能力 | 说明 |
|---|---|
| ReAct 循环 | 推理-行动-观察 |
| Planner (Plan-and-Execute) | 任务拆解+replan |
| Reflector (Evaluator-Optimizer) | 生成→评审→改进 |
| 多 Agent (Supervisor) | 主管-专家协作 |
| A2A 协议 | 跨智能体通信 |
| Skills 技能 | 可复用技能包 + 导入导出 |
| 长短期记忆 | 会话记忆 + 向量记忆 + RAG |
| 人机协同 (HITL) | LangGraph interrupt 审批 |

## 四、模型与工程
| 能力 | 说明 |
|---|---|
| 多 Provider 适配 | OpenAI/Anthropic/Gemini/Ollama/本地 |
| 模型路由/降级/负载均衡 | 多档位 fallback |
| LLM 缓存 | 精确+语义缓存 |
| 结构化输出校验 | JSON Schema 校验管道 |
| 提示词管理 | DB 版本/A-B/灰度 |
| 文本处理 | 关键词/摘要/归一化/去重 |
| 错误码体系 | 三段式报错 |

## 五、知识检索
| 能力 | 说明 |
|---|---|
| 向量检索 | ChromaDB |
| 混合检索 | BM25 + 向量 + RRF |
| Rerank 重排 | Cohere/Jina/BGE |
| 知识库管理 | 上传/解析/分块/检索 |
| 引用溯源 | 答案关联来源 |

## 六、安全与质量
| 能力 | 说明 |
|---|---|
| 提示注入防护 | InputGuard + 高级检测 |
| 输出护栏/PII 脱敏 | OutputGuard |
| 登录风控 + MFA | 暴力锁定 + 双因子 |
| 审计哈希链 | 防篡改 |
| 评估/评测 | LLM-as-Judge / RAGAS |
| AI 安全红队 | 威胁用例 + 演练 |
| 可观测性 | Trace / Metrics / 告警 |

## 七、垂直能力（本主题特色）
- **人才价值引擎**（多体系类型：淘汰制/培养制/晋升制/认证制/灵活用工）
- **对话控制台**：在对话里完成全部程序调用与更改
- 企业治理（公告/工单/数据资产/管道/容灾）

> 全部能力均有后端实现 + 路由 + 测试，`make check-backend` 质量门禁保障不回归。
