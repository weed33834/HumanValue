<p align="center">
  <img src="docs/assets/logo.svg" width="140" alt="HumanValue" />
</p>

<h1 align="center">HumanValue</h1>

<p align="center">
  <strong>人材価値インテリジェンス・プラットフォーム</strong><br/>
  会話型 AI · エージェントツール · 自動人事評価 · 多視点評価
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-blue.svg" alt="ライセンス" /></a>
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/Node-20+-339933?logo=nodedotjs&logoColor=white" alt="Node 20+" />
  <img src="https://img.shields.io/badge/FastAPI-0.139+-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Vue_3-4FC08D?logo=vuedotjs&logoColor=white" alt="Vue 3" />
  <a href="CHANGELOG.md"><img src="https://img.shields.io/badge/version-1.0.10-blue.svg" alt="バージョン 1.0.10" /></a>
</p>

<p align="center">
  <strong>言語切替:</strong> <a href="README.md">English</a> · <a href="README.zh-CN.md">中文</a> · <a href="README.ja-JP.md">日本語</a>
</p>

<p align="center">
  <img src="docs/assets/demo/humanvalue-promo.gif" width="640" alt="HumanValue デモ" />
</p>

---

**HumanValue** は、AI を活用した人材価値の定量化・成長プラットフォームです。会話型 AI、エージェントツール、自動多視点評価を統合し、マネージャーと人事が一人ひとりの価値を理解・育成・最大化することを支援します。UI は**英語を基本**とし、**中文 / 日本語**を切替可能です。

## 主な機能

- **会話型 AI とチャットコンソール** — AI アシスタントがシステムの操作コンソールを兼ね、チャット内で人材分析・公告作成・チケット管理・データパイプライン実行・バックアップなどを実行できます。
- **人材価値エンジン** — 理論に基づく 10 の分析：9ボックス分類、キーマン/単一障害点リスク、パレート集中度、チーム効率、インセンティブ戦略、報酬競争力、後継計画、バーンアウト警告、スキル適合と再配置、四半期レビュー。
- **多体系タイプ** — 同じエンジンが企業（淘汰制）・大学（育成制）・公共機関（昇進制）・研修（認定制）・プラットフォーム（柔軟雇用制）に適応します。
- **エンタープライズ統治** — MFA、ログイン防護、公告、チケット、データ資産、データパイプライン、災害復旧バックアップ、AI セキュリティレッドチーム。
- **汎用エージェント能力** — ReAct、プランナー、リフレクター、マルチエージェント、MCP クライアント/サーバー、A2A、ブラウザ自動化、スキル、記憶と RAG、SSE ストリーミング、コンテキスト圧縮など。

## 製品プレビュー

| 人材ダッシュボード | 人材価値エンジン | AI アシスタント（チャットコンソール） |
|:---:|:---:|:---:|
| ![人材ダッシュボード](docs/assets/demo/02-dashboard.png) | ![人材価値](docs/assets/demo/04-talent-value.png) | ![AI アシスタント](docs/assets/demo/05-chat-complex.png) |

| コマンドパレット | チャットで公告作成 | ダークモード |
|:---:|:---:|:---:|
| ![コマンドパレット](docs/assets/demo/03-command-palette.png) | ![公告作成](docs/assets/demo/06-console-announcement.png) | ![ダークモード](docs/assets/demo/09-dark.png) |

> 完全なデモは [デモ展示](docs/demo-showcase.md) をご覧ください。

## クイックスタート

```bash
git clone https://github.com/weed33834/HumanValue.git
cd HumanValue
cp backend/.env.example backend/.env
docker compose up -d --build
```

## ドキュメント

| ドキュメント | 説明 |
|---|---|
| [デモ展示](docs/demo-showcase.md) | 録画・スクリーンショット |
| [エージェント能力](docs/universal-agent.md) | 汎用エージェント機能 |
| [チャットコンソール](docs/chat-console.md) | チャットでの操作ガイド |
| [ショートカット](docs/shortcuts.md) | ショートカットとヒント |
| [エラーコード](docs/error-codes.md) | エラーコードハンドブック |
| [導入ガイド](docs/adoption-enterprise-academia.md) | 企業・大学向け段階的導入 |
| [コンプライアンス](docs/compliance-employee-rights.md) | PIPL/GDPR 自動意思決定対応 |

## リポジトリ

| プラットフォーム | URL |
|---|---|
| GitHub（主） | https://github.com/weed33834/HumanValue |
| GitCode（ミラー） | https://gitcode.com/badhope/HumanValue |
| Gitee（ミラー） | https://gitee.com/badhope/HumanValue |

## ライセンス

Apache License 2.0。詳細は [LICENSE](LICENSE)。
