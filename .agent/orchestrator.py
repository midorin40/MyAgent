import os
import time
import re
import sys

# パス設定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TASK_FILE = os.path.join(BASE_DIR, "task.md")
ORDERS_DIR = os.path.join(BASE_DIR, "orders")
RESULTS_DIR = os.path.join(BASE_DIR, "results")

def log(msg):
    # flush=True を追加してリアルタイムでログが見えるようにする
    print(f"[{time.strftime('%H:%M:%S')}] [ORCHESTRATOR] {msg}", flush=True)

def get_task_state():
    if not os.path.exists(TASK_FILE):
        return []
    try:
        with open(TASK_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        log(f"Error reading task file: {e}")
        return []
    
    tasks = []
    for line in lines:
        if "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        # ヘッダーや区切り線をスキップ
        if len(parts) < 6 or parts[1] == "#" or parts[1].startswith("---"):
            continue
            
        task_id = parts[1]
        content = parts[2]
        agent = parts[3]
        deps = parts[4]
        status_part = parts[5]
        
        # ステータス [ ] から中身を抽出
        status_match = re.search(r"\[( |x|/|X)\]", status_part)
        if status_match:
            tasks.append({
                "id": task_id,
                "content": content,
                "agent": agent,
                "deps": deps,
                "status": status_match.group(1)
            })
            # log(f"Parsed task {task_id}: status=[{status_match.group(1)}]")
            
    return tasks

def update_task_status(task_id, status):
    log(f"Updating task {task_id} status to [{status}]")
    try:
        with open(TASK_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        new_lines = []
        for line in lines:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 6 and parts[1] == task_id:
                # [ ] 部分だけ置換
                line = re.sub(r"\[( |x|/|X)\]", f"[{status}]", line)
            new_lines.append(line)
            
        with open(TASK_FILE, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    except Exception as e:
        log(f"Error updating task status: {e}")

def dispatch_task(task):
    agent_raw = task["agent"]
    agent_clean = agent_raw.lower().replace(" ", "")
    order_file = os.path.join(ORDERS_DIR, f"{agent_clean}_{task['id']}.md")
    
    instruction = f"""# タスク指示書 (Task ID: {task['id']})

【あなたの役割】
{agent_raw}

【タスク内容】
{task['content']}

【入力情報】
前回の成果物があれば .agent/results/ フォルダを確認してください。

【出力先】
.agent/results/result_{agent_clean}_{task['id']}.md

【完了時のアクション】
必ず実行完了後に `.agent/results/` に報告書を作成してください。
（※報告書のファイル名は result_{agent_clean}_{task['id']}.md としてください）
"""
    try:
        with open(order_file, "w", encoding="utf-8") as f:
            f.write(instruction)
        log(f"DISPATCHED Task {task['id']} to {agent_clean}")
        update_task_status(task["id"], "/")
    except Exception as e:
        log(f"Error dispatching task: {e}")

def monitor():
    log("Monitoring started with improved parser (split-based)")
    while True:
        try:
            tasks = get_task_state()
            if not tasks:
                time.sleep(5)
                continue

            completed_ids = [t["id"] for t in tasks if t["status"] in ["x", "X"]]

            for task in tasks:
                # 1. 完了チェック (resultsフォルダに成果物があるか)
                agent_clean = task["agent"].lower().replace(" ", "")
                result_file = f"result_{agent_clean}_{task['id']}.md"
                
                if os.path.exists(os.path.join(RESULTS_DIR, result_file)) and task["status"] not in ["x", "X"]:
                    log(f"Detected result for Task {task['id']} ({task['agent']})")
                    update_task_status(task["id"], "x")
                    continue

                # 2. 次のタスクのディスパッチ
                if task["status"] == " ":
                    deps_raw = task["deps"].replace("#", "").strip()
                    if not deps_raw or deps_raw == "なし":
                        deps = []
                    else:
                        deps = [d.strip() for d in deps_raw.split(",")]
                    
                    all_deps_met = True
                    for d in deps:
                        if d not in completed_ids:
                            all_deps_met = False
                            break
                    
                    if all_deps_met:
                        dispatch_task(task)
        except Exception as e:
            log(f"Monitor loop error: {e}")

        time.sleep(5)

if __name__ == "__main__":
    monitor()
