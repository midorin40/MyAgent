#!/bin/bash
# Universal Agent Hub v1.0 Bootstrap Script

echo "🚀 Universal Agent Hub のセットアップを開始します..."

# 1. 必要ディレクトリの作成
mkdir -p .agent/orders .agent/processing .agent/results .agent/artifacts/drafts .agent/artifacts/logs .agent/artifacts/screen .agent/artifacts/questions .agent/scripts

# 2. プレースホルダーの作成
touch .agent/orders/.gitkeep .agent/processing/.gitkeep .agent/results/.gitkeep .agent/artifacts/drafts/.gitkeep

# 3. 監視ループプロンプトの初期化（もしなければ）
if [ ! -f .agent/agent_loop_prompt.md ]; then
    echo "📓 agent_loop_prompt.md を作成中..."
    cat <<EOF > .agent/agent_loop_prompt.md
あなたは監視ループモードです。
以下のディレクトリをポーリング（監視）してください。
- 監視先: .agent/orders/
- 自分宛のファイル（例: claude_*.md）があればそれを .agent/processing/ に移動して実行。
- 完了したら結果を .agent/results/ に書き出し、task.md のステータスを更新せよ。
EOF
fi

# 4. オーケストレーターの配置確認
if [ ! -f .agent/orchestrator.py ]; then
    echo "⚠️ orchestrator.py が見つかりません。配置してください。"
fi

echo "✅ セットアップが完了しました。"
echo "次に 'python .agent/orchestrator.py' を起動し、各エージェントのコンソールで監視ループを開始してください。"
