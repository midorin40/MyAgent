---
name: multi-agent-browser-sync
description: Skill for coordinating multiple AI agents (Claude, Gemini, Codex) for end-to-end development, browser-based verification, and article creation.
---

# Multi-Agent Orchestration Skill

このSkillは、Antigravity（オーケストレーター）が複数のAIエージェントに対し、タスクを動的に計画・分割・割り振り・監視するためのプロトコルです。

> [!IMPORTANT]
> 役割分担は固定ではありません。毎回のタスクに対し、Phase 0 で最適な分担を計画してからディスパッチしてください。

---

## 全体フロー

```
Phase 0: 計画（Plan）    → タスク分析、サブタスク分解、役割割当
Phase 1: 配備（Dispatch） → 各エージェントへプロンプト送信
Phase 2: 監視（Monitor）  → task.md で進捗追跡、ブロッカー解消
Phase 3: 統合（Integrate） → 成果物の収集・統合・最終確認
```

---

## Phase 0: 計画（Plan）

**目的**: ユーザーの指示を分析し、最適なサブタスク分解と役割割当を決定する。

### Step 0-1: タスク分析
ユーザーの指示から以下を抽出する：
- **ゴール**: 最終的な成果物は何か（例: note記事、デプロイ済みアプリ、テストレポート）
- **前提条件**: 環境は整っているか、認証情報は必要か
- **依存関係**: サブタスク間の順序制約はあるか（例: インストール→テスト→記事）

### Step 0-2: サブタスク分解
タスクを独立したサブタスクに分割する。分割基準：
- **直列（Sequential）**: 前のタスクの出力が必要 → 順番に実行
- **並列（Parallel）**: 独立して同時実行可能 → 同時ディスパッチ

### Step 0-3: 役割割当
以下のエージェント能力マトリクスを参照し、各サブタスクに最適なエージェントを割り当てる。

#### エージェント能力マトリクス

| 能力 | Claude Code | Gemini CLI | Codex | Antigravity (私) |
|---|---|---|---|---|
| シェル操作・環境構築 | ◎ | ○ | ○ | △ (run_command) |
| コード読解・修正 | ◎ | ◎ | ◎ | ○ |
| ファイル生成・編集 | ◎ | ◎ | ◎ | ◎ |
| ブラウザ操作・CDP | ✗ | ✗ | ✗ | ◎ (唯一) |
| スクリーンショット撮影 | ✗ | ✗ | ✗ | ◎ (唯一) |
| Web検索・情報収集 | ○ | ◎ | ○ | ◎ |
| 長文ドキュメント執筆 | ◎ | ◎ | ○ | ◎ |
| テスト実行・CI/CD | ◎ | ○ | ◎ | ○ |
| 画像生成 | ✗ | ✗ | ✗ | ◎ (唯一) |
| MCP連携 | ✗ | ✗ | ✗ | ◎ |

**凡例**: ◎最適 ○可能 △制限あり ✗不可

#### 割当ルール
1. **ブラウザ操作・スクリーンショット・画像生成** → 必ず Antigravity（私）が担当
   - **【重要】Chromeブラウザを立ち上げる際、あるいはログイン操作を行う際は、必ず `midorincrypto20@gmail.com` のアカウントを使用すること。**
2. **重い環境構築（npm install, docker build等）** → Claude Code が最適（並列ファイル操作が高速）
3. **コード実行・スクリプト検証** → 必ず **OpenSandbox**（隔離コンテナ）上で実行すること。
   - `docker exec agent-sandbox-server python <file>` などのコマンドを使用。
4. **コードレビュー・リファクタリング** → 空いているエージェントに割当
5. **記事・ドキュメント執筆** → 得意なエージェントを選定（Claude Code / Gemini が得意）
6. **依存関係がある場合** → 先行タスクのエージェントが `task.md` を更新してから次をディスパッチ

### Step 0-4: 計画書の作成
以下のフォーマットで `.agent/task.md` を作成し、全エージェントが参照できるようにする。

```markdown
# マルチエージェント実行計画
## 指示: [ユーザーの元の指示]
## 実行モード: [直列 / 並列 / ハイブリッド]

### サブタスク一覧
| # | サブタスク | 担当 | 依存 | 状態 |
|---|-----------|------|------|------|
| 1 | [内容]    | [エージェント名] | なし | [ ] |
| 2 | [内容]    | [エージェント名] | #1   | [ ] |
| 3 | [内容]    | [エージェント名] | #2   | [ ] |

### 成果物の格納先
- スクリーンショット: `artifacts/screen/`
- ログ: `artifacts/logs/`
- 記事原稿: `artifacts/drafts/`
```

---

## Phase 1: 配備（Dispatch）【ファイル経由版】

各エージェントへの指示は直接ターミナルに打ち込むのではなく、`orders/` フォルダへの指示書出力によって非同期に行われます（deer-flow 方式）。

### ディスパッチ手順

1. **現在の状態読取**: `task.md` のうち、依存関係がクリアされていて現在実行可能なタスクを特定する。
2. **指示書の作成**: 担当エージェントごとに、実行すべき具体的な指示書（Markdown）を構築する。
   - ファイル名規則: `[担当エージェント名]_[タスクID].md` （例: `claude_1.md`）
   - 保存先: `.agent/orders/`
3. **ポーリング**: 各ターミナルで待機中のエージェント（`agent_loop_prompt.md`を読み込み済みの状態）が自動的にこのファイルを拾い、処理を開始します。

### インストラクション（指示書）テンプレート
出力する指示書ファイル（例: `.agent/orders/claude_1.md`）の中身：

```markdown
# タスク指示書 (Task ID: {task_number})

【あなたの役割】
{role_description}

【タスク内容】
{task_description}

【入力情報】
{input_data_or_previous_output_path}

【出力先】
.agent/results/result_{task_id}.md

【完了時のアクション】
必ず以下のファイルの該当行を `[x]` に更新してください:
ファイル: c:\AI\Agent\.agent\task.md
該当行: サブタスク #{task_number}

【重要な制約】
- 他のエージェントの担当ファイルを編集しないこと
- 疑問があれば `artifacts/questions/` 配下に書き出すこと
```

---
## Phase 2: 監視（Monitor）

### 進捗確認の方法
1. `task.md` を定期的に読み取り、各サブタスクの状態を確認する。
2. 直列タスクの完了を検知したら、次のエージェントをディスパッチする。
3. エラーや質問が `artifacts/questions/` に出力されていれば対応する。

### ブロッカーの解消
- **エージェントが停止している場合**: ターミナルの出力を `read_terminal` で確認し、追加指示を `send_command_input` で送信。
- **ブラウザ操作が必要な場合**: 私（Antigravity）が `browser_subagent` で対応。

---

## Phase 3: 統合（Integrate）

1. 全サブタスクの完了を確認。
2. `artifacts/` 配下の成果物を収集・統合。
3. 最終成果物をユーザーに提示（`notify_user`）。
4. 必要に応じてブラウザで投稿・公開作業を実施。

---

## 実行例

### 例: 「○○アプリを検証してnote記事にして」

**Phase 0 の出力（計画）:**

| # | サブタスク | 担当 | 依存 | 理由 |
|---|-----------|------|------|------|
| 1 | リポジトリのクローンと環境構築 | Claude Code | なし | シェル操作が最も高速 |
| 2 | アプリ起動と動作テスト・スクショ | Antigravity | #1 | ブラウザ操作が必要（CDP） |
| 3 | テスト結果の分析とバグリスト作成 | Codex | #2 | コード分析が得意 |
| 4 | note記事の執筆 | Gemini CLI | #2, #3 | スクショとバグリストを入力に執筆 |
| 5 | note.com への下書き投稿 | Antigravity | #4 | ブラウザ操作が必要 |

**Phase 1**: #1 を Claude Code にディスパッチ → 完了後 #2 を実行 → ...

---

## ディレクトリ構造

```
c:\AI\Agent\.agent\
├── task.md                              # 共有ステート
├── orchestrator.py                      # 自律監視エンジン (Python)
├── agent_loop_prompt.md                 # エージェント用待機プロンプト
├── scripts/
│   └── setup_sandbox.py                 # Sandbox構築スクリプト
├── skills/
│   └── multi-agent-browser-sync/
│       └── SKILL.md                     # オーケストレーション定義
├── orders/                              # 発行された指示書
├── processing/                          # 各エージェントが作業中の指示書
├── results/                             # 完了したタスクの報告書
└── artifacts/                           # 成果物格納
    ├── screen/                          # スクリーンショット
    ├── logs/                            # 実行ログ
    ├── drafts/                          # 記事原稿
    └── questions/                       # 質問
```
