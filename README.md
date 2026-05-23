# 基于LightGBM的大学生体质健康分类系统

## 项目说明

- **特征体系**：选取的11维核心特征
- **数据划分**：7:2:1 分层抽样
- **模型训练与超参数优化**：GridSearchCV + 五折交叉验证（论文3.3节）
- **对比模型**：随机森林、逻辑回归（论文4.1节）
- **类别名称**：优秀、良好、及格、不及格

## 目录结构

```
PROJECT (2)/
├── data.xlsx                     # 原始体测数据（12万+条）
├── backend/
│   ├── requirements.txt          # Python依赖
│   ├── ml/
│   │   ├── config.py             # 特征配置、标签映射
│   │   ├── preprocess.py         # 数据预处理（IQR异常值等）
│   │   └── train.py              # 训练脚本（GridSearchCV）
│   ├── app/
│   │   ├── main.py               # FastAPI入口
│   │   ├── schemas.py            # Pydantic接口模型
│   │   └── service.py            # 模型加载与推理
│   └── artifacts/                # 训练产物（自动生成）
│       ├── imputer.joblib
│       ├── scaler.joblib
│       ├── lgb_model.joblib
│       ├── metrics.json
│       └── model_meta.json
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── App.vue               # Vue3主组件
        └── main.js               # 入口
```

## 快速开始

### 1. 训练模型

```bash
cd backend
pip install -r requirements.txt
python -m ml.train
```

### 2. 启动后端API

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000/docs 查看 Swagger 交互式接口文档。

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173 使用Web界面。

## API接口

### POST /predict

请求示例：
```json
{
  "test_grade": 1,
  "gender": 1,
  "height_cm": 178.0,
  "weight_kg": 67.4,
  "bmi": 21.27,
  "vital_capacity_ml": 4319,
  "run_50m_s": 7.8,
  "standing_long_jump_cm": 211,
  "sit_reach_cm": 8.1,
  "long_run_sec": 271,
  "strength_count": 10
}
```

响应示例：
```json
{
  "ok": true,
  "data": {
    "label_id": 1,
    "label_cn": "良好",
    "label_en": "Good",
    "probabilities": {
      "优秀": 0.0123,
      "良好": 0.8456,
      "及格": 0.1401,
      "不及格": 0.0020
    }
  },
  "error": null
}
```
