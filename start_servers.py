"""一键启动前后端服务（独立进程）"""
import subprocess
import sys
import os
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable

# 启动后端
backend = subprocess.Popen(
    [PYTHON, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
    cwd=os.path.join(ROOT, "backend"),
    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
)
print(f"后端已启动 (pid={backend.pid}) — http://127.0.0.1:8000/docs")

# 等后端就绪
time.sleep(3)

# 启动前端
npm_cmd = "npx.cmd" if sys.platform == "win32" else "npx"
frontend = subprocess.Popen(
    [npm_cmd, "vite", "--host"],
    cwd=os.path.join(ROOT, "frontend"),
    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
)
print(f"前端已启动 (pid={frontend.pid}) — http://127.0.0.1:5173")
print("\n按 Enter 关闭服务...")
input()

# 清理
frontend.terminate()
backend.terminate()
print("服务已停止")
