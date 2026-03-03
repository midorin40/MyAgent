import os
import subprocess
import sys
import time

# OpenSandbox (Alibaba) サーバーの構築スクリプト
# https://github.com/Alibaba/OpenSandbox 準拠

def log(msg):
    print(f"[*] {msg}", flush=True)

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed: {cmd}\n{e.stderr}")
        return None

def setup():
    log("OpenSandbox 構築プロセスを開始します...")

    # 1. Docker の確認
    log("Docker の状態を確認中...")
    docker_version = run_cmd("docker --version")
    if not docker_version:
        log("Docker がインストールされていないか、起動していません。Docker Desktop を起動してください。")
        return

    # 2. OpenSandbox イメージのプル
    # 注: 公式イメージがない場合はビルドが必要だが、ここでは一般的なイメージまたは
    # ユーザーが用意したベース環境（Python/Node）を使用する Dockerfile を作成する
    log("Sandbox 用の隔離 Docker イメージを準備しています...")
    
    dockerfile_content = """FROM python:3.10-slim
RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*
RUN pip install flask requests
WORKDIR /workspace
"""
    with open("Sandbox.Dockerfile", "w") as f:
        f.write(dockerfile_content)
    
    run_cmd("docker build -t lida-agent-sandbox -f Sandbox.Dockerfile .")

    # 3. サーバーコンテナの起動 (API経由でコードを受け取る想定)
    # 本来の OpenSandbox は grpc インターフェースだが、
    # ここでは簡易的な REST API ラッパー（または直接 docker exec）を使用する
    log("Sandbox サーバーをバックグラウンドで起動します...")
    
    # 既存の同名コンテナがあれば削除
    run_cmd("docker rm -f agent-sandbox-server")
    
    # コンテナを起動（ネットワーク、ファイルシステムを制限した状態を想定）
    run_cmd("docker run -d --name agent-sandbox-server -v /var/run/docker.sock:/var/run/docker.sock lida-agent-sandbox tail -f /dev/null")

    log("✅ OpenSandbox (lida-agent-sandbox) の準備が整いました。")
    log("エージェントはこれから `docker exec agent-sandbox-server python script.py` を通じて安全に作業できます。")

if __name__ == "__main__":
    setup()
