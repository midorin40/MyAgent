# 🪐 Universal Agent Hub

**AIエージェントの自律型オフィス環境テンプレート**

Claude Code・Gemini CLI・Codex CLI の3エージェントが、ファイルベースの非同期連携（deer-flow方式）で自律的にタスクをリレーするための環境です。

---

## ✨ 特徴

- **マルチエージェント連携**: 複数のAIエージェントが `orders/` → `results/` のフォルダを介して自動バトンパス
- **OpenSandbox**: Docker コンテナによる安全なコード実行環境
- **完全自走モード**: PowerShell ポーリングスクリプトにより、人間の介入なしで 24 時間稼働
- **テンプレート化済**: `bootstrap.sh` 一発で新規環境を構築可能

---

## 🚀 クイックスタート

### 1. リポジトリのクローン

```bash
git clone <this-repo-url>
cd Agent
```

### 2. 環境のブートストラップ

```bash
bash .agent/bootstrap.sh
```

### 3. OpenSandbox の構築（任意）

```bash
python .agent/scripts/setup_sandbox.py
```

### 4. オーケストレーターの起動

```bash
python .agent/orchestrator.py
```

### 5. エージェント監視ループの起動（各ターミナルで）

```powershell
# Claude Code
powershell -ExecutionPolicy Bypass -File .agent/claude_agent_loop.ps1

# Gemini CLI
powershell -ExecutionPolicy Bypass -File .agent/gemini_agent_loop.ps1

# Codex CLI
powershell -ExecutionPolicy Bypass -File .agent/codex_agent_loop.ps1
```

### 6. タスクの投入

`.agent/task_template.md` を `.agent/task.md` にコピーして編集し、サブタスクを定義します。
オーケストレーターが自動的に依存関係を解析し、各エージェントに指示書を配布します。

---

## 📂 ディレクトリ構成

```
.agent/
├── orchestrator.py          # 司令塔（タスク監視 & 指示書生成）
├── bootstrap.sh             # 環境セットアップスクリプト
├── task_template.md          # タスク定義テンプレート
├── agent_loop_prompt.md      # エージェント監視ループ用プロンプト
├── claude_agent_loop.ps1     # Claude Code 自走スクリプト
├── gemini_agent_loop.ps1     # Gemini CLI 自走スクリプト
├── codex_agent_loop.ps1      # Codex CLI 自走スクリプト
├── scripts/
│   └── setup_sandbox.py      # OpenSandbox 構築スクリプト
├── skills/
│   └── multi-agent-browser-sync/  # ブラウザ連携スキル
├── workflows/
│   ├── dispatch.md           # /dispatch ワークフロー
│   ├── plan.md               # /plan ワークフロー
│   └── status.md             # /status ワークフロー
├── orders/                   # エージェントへの指示書（自動生成）
├── processing/               # 処理中タスク（一時）
├── results/                  # 完了した成果物
├── completed/                # アーカイブ済みタスク
├── logs/                     # 実行ログ
└── artifacts/
    ├── drafts/               # 記事等の下書き
    ├── screen/               # スクリーンショット
    ├── logs/                 # アーティファクトログ
    └── questions/            # エージェントからの質問
```

---

## 🔗 関連リンク

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview)
- [Gemini CLI](https://github.com/google-gemini/gemini-cli)
- [Codex CLI](https://github.com/openai/codex)
- [deer-flow](https://github.com/bytedance/deer-flow)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
