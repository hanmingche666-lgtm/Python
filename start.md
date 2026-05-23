# 运行说明

## 方式一：一键启动（推荐）

双击运行脚本即可，会自动安装依赖：

| 脚本 | 作用 |
|------|------|
| `backend/run.bat` | 启动后端 API（端口 8000） |
| `frontend/run.bat` | 启动前端界面（端口 5173） |
| `start_servers.py` | 同时启动前后端 |

## 方式二：手动启动

### 1. 启动后端

```bash
cd backend
pip install -r requirements.txt        # 仅首次
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

访问 http://127.0.0.1:8000/docs 查看 API 文档。

### 2. 启动前端

```bash
cd frontend
npm install                            # 仅首次
npx vite --host
```

访问 http://127.0.0.1:5173 使用界面。

## 问题排查

端口被占用：
```bash
netstat -ano | findstr :8000
taskkill /pid 你的PID /f
```
