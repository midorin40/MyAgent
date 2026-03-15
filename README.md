# Universal Agent Hub

`claude`、`gemini`、`codex` を対象にした、ファイルベースのマルチエージェント実行テンプレートです。

このリポジトリは再利用前提です。制御プレーンは `.agent/` に集約し、`OpenSandbox/` と `deer-flow/` を同居させることで、新しい環境でも同じ構成を再現できるようにしています。

## 概要
- `.agent/task.md` から静的タスクを配布できる
- `.agent/requests/*.json` 経由で動的にサブタスクを委譲できる
- 子タスク完了後に callback タスクを再投入できる
- ログ、成果物、状態ファイルを `.agent/` 以下に集約できる

## クイックスタート
```bash
agent setup
```

このコマンドで以下をまとめて実行します。
1. `.agent/` の不足ディレクトリとプレースホルダを作成
2. ローカル環境と必須リポジトリのチェック
3. 環境固有のセットアップガイド生成

## `agent` コマンド
このリポジトリにはローカル実行用の `agent` エントリポイントが入っています。

- Windows: `agent.cmd`
- POSIX シェル: `./agent`
- Python 直実行: `python agent.py`

主なコマンド:
- `agent setup`
- `agent setup --with-sandbox`
- `agent check`
- `agent guide`
- `agent orchestrator`
- `agent orchestrator --once`
- `agent loop codex`
- `agent loop claude`
- `agent loop gemini`

## 初期セットアップ
新しい環境では、まず必要リポジトリを配置してから `agent setup` を実行します。

```bash
git clone https://github.com/alibaba/OpenSandbox.git
git clone https://github.com/bytedance/deer-flow.git
agent setup
```

OpenSandbox 補助チェックも続けて回したい場合:

```bash
agent setup --with-sandbox
```

## 実行方法
オーケストレータを起動:

```bash
agent orchestrator
```

1 サイクルだけ実行:

```bash
agent orchestrator --once
```

各 worker loop は別ターミナルで起動:

```powershell
agent loop codex
agent loop claude
agent loop gemini
```

各 loop はスクリプト自身の位置からリポジトリルートを解決します。CLI 名が環境ごとに違う場合は、`CLAUDE_CMD`、`GEMINI_CMD`、`CODEX_CMD` で上書きできます。

## ワークスペース設定
テンプレートは [`.agent/workspace.json`](/C:/AI/Agent/.agent/workspace.json) を優先し、存在しない場合は [`.agent/workspace.template.json`](/C:/AI/Agent/.agent/workspace.template.json) を読みます。

ここで定義するもの:
- 各ツールのコマンド名
- 同居させるリポジトリ
- 必須リポジトリか任意リポジトリか
- セットアップガイドに出す clone 元 URL

現在の設定では以下を必須にしています。
- `OpenSandbox`: `https://github.com/alibaba/OpenSandbox.git`
- `deer-flow`: `https://github.com/bytedance/deer-flow.git`

## 主要ディレクトリ
- `.agent/orders`: 配布待ちタスク
- `.agent/processing`: 実行中タスク
- `.agent/results`: 結果レポートと summary
- `.agent/requests`: 動的委譲リクエスト
- `.agent/state`: 動的委譲の状態管理
- `.agent/artifacts`: ログ、下書き、画面キャプチャ、環境レポート
- `OpenSandbox/`: サンドボックス実行基盤
- `deer-flow/`: ワークフロー設計の参照実装

## 生成されるファイル
`agent setup` や `agent check` を実行すると、以下が更新されます。

- 環境レポート: [`.agent/artifacts/logs/environment_report.json`](/C:/AI/Agent/.agent/artifacts/logs/environment_report.json)
- セットアップガイド: [`.agent/artifacts/logs/setup_guide.md`](/C:/AI/Agent/.agent/artifacts/logs/setup_guide.md)

## OpenSandbox
`OpenSandbox/` が存在する場合、このテンプレートはそれをサンドボックス実行基盤の参照として扱います。上流の最小起動手順は以下です。

```bash
uv pip install opensandbox-server
opensandbox-server init-config ~/.sandbox.toml --example docker
opensandbox-server
```

詳細は [OpenSandbox/README.md](/C:/AI/Agent/OpenSandbox/README.md) を参照してください。

## 動的委譲
エージェントは `submit_dispatch.py` を使って複数エージェントへサブタスクを配布できます。

```bash
python .agent/scripts/submit_dispatch.py \
  --requester codex \
  --parent-task-id codex_parent_1 \
  --subtask "{\"label\":\"research\",\"agent\":\"claude\",\"content\":\"Collect the relevant facts.\"}" \
  --subtask "{\"label\":\"verify\",\"agent\":\"gemini\",\"content\":\"Cross-check the findings.\"}" \
  --callback-agent codex \
  --callback-content "Read the summary and integrate the delegated outputs."
```

オーケストレータは以下を行います。
- 子タスクを各 agent に配布
- 全結果ファイルを待機
- summary を `.agent/results/` に生成
- callback 指定があれば親フロー用タスクを再投入

## 補足
- Windows では `codex exec` が権限不足で失敗する場合があります。その場合は `Codex CLI` を実行できる権限のあるコンテキストで worker を起動してください。
- 新しい環境へ持っていく場合は、まず `workspace.json` を調整し、その後に `agent setup` を実行するのが最短です。
