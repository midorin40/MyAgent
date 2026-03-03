@echo off
REM ===========================
REM Universal Agent Hub v1.0 Bootstrap Script (Windows)
REM ===========================

echo 🚀 Universal Agent Hub のセットアップを開始します...

REM 1. 必要ディレクトリの作成
if not exist ".agent\orders" mkdir ".agent\orders"
if not exist ".agent\processing" mkdir ".agent\processing"
if not exist ".agent\results" mkdir ".agent\results"
if not exist ".agent\completed" mkdir ".agent\completed"
if not exist ".agent\logs" mkdir ".agent\logs"
if not exist ".agent\artifacts\drafts" mkdir ".agent\artifacts\drafts"
if not exist ".agent\artifacts\logs" mkdir ".agent\artifacts\logs"
if not exist ".agent\artifacts\screen" mkdir ".agent\artifacts\screen"
if not exist ".agent\artifacts\questions" mkdir ".agent\artifacts\questions"
if not exist ".agent\scripts" mkdir ".agent\scripts"

REM 2. プレースホルダの作成
if not exist ".agent\orders\.gitkeep" type nul > ".agent\orders\.gitkeep"
if not exist ".agent\processing\.gitkeep" type nul > ".agent\processing\.gitkeep"
if not exist ".agent\results\.gitkeep" type nul > ".agent\results\.gitkeep"
if not exist ".agent\artifacts\drafts\.gitkeep" type nul > ".agent\artifacts\drafts\.gitkeep"

REM 3. オーケストレーター確認
if not exist ".agent\orchestrator.py" (
    echo ⚠️ orchestrator.py が見つかりません。リポジトリの .agent/ を確認してください。
)

echo.
echo ✅ セットアップが完了しました！
echo.
echo 次のステップ:
echo   1. python .agent/orchestrator.py          ^(司令塔を起動^)
echo   2. 各ターミナルで *_agent_loop.ps1 を起動  ^(エージェント自走モード^)
echo   3. .agent/task_template.md → task.md にコピーしてタスクを定義
echo.
