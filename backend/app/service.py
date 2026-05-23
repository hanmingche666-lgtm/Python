# -*- coding: utf-8 -*-
"""预测服务：模型加载、推理、结果格式化"""
from __future__ import annotations

import sys
from pathlib import Path

import joblib
import numpy as np

from app.schemas import PredictIn
from ml.config import CLASS_NAMES_CN, CLASS_NAMES_EN, FEATURE_COLUMNS


def _artifacts_dir() -> Path:
    """兼容 PyInstaller 打包后的路径查找"""
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
    else:
        # service.py -> backend/app/ -> backend/ -> project_root
        base = Path(__file__).resolve().parents[2]
    # 尝试多个可能的位置
    candidates = [
        base / "artifacts",
        base / "backend" / "artifacts",
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]  # 默认返回第一个，让它报 FileNotFoundError


_ARTIFACTS = _artifacts_dir()
_IMPUTER = _ARTIFACTS / "imputer.joblib"
_SCALER = _ARTIFACTS / "scaler.joblib"
_MODEL = _ARTIFACTS / "lgb_model.joblib"

_imputer = None
_scaler = None
_model = None

# 论文表3.1特征列名 → PredictIn属性名映射（11维）
_COL_TO_ATTR = {
    "测试年级": "test_grade",
    "性别": "gender",
    "身高cm": "height_cm",
    "体重kg": "weight_kg",
    "BMI": "bmi",
    "肺活量ml": "vital_capacity_ml",
    "50M跑（s）": "run_50m_s",
    "立定跳远cm": "standing_long_jump_cm",
    "坐位体前屈cm": "sit_reach_cm",
    "长跑秒数（s）": "long_run_sec",
    "引体仰卧个数": "strength_count",
}


def load_artifacts() -> None:
    global _imputer, _scaler, _model
    for p, name in [(_IMPUTER, "imputer"), (_SCALER, "scaler"),
                    (_MODEL, "model")]:
        if not p.exists():
            raise FileNotFoundError(
                f"未找到{name}文件，请先在 backend 目录执行: python -m ml.train"
            )
    _imputer = joblib.load(_IMPUTER)
    _scaler = joblib.load(_SCALER)
    _model = joblib.load(_MODEL)


def _pydantic_to_row(p: PredictIn) -> np.ndarray:
    """将Pydantic输入按FEATURE_COLUMNS顺序组装为特征行"""
    vals = []
    for col in FEATURE_COLUMNS:
        attr = _COL_TO_ATTR[col]
        v = getattr(p, attr)
        if v is None:
            v = np.nan
        vals.append(float(v))
    return np.array(vals, dtype=float).reshape(1, -1)


def predict_one(p: PredictIn) -> tuple[int, np.ndarray]:
    """单样本预测：填补→标准化→推理"""
    if _imputer is None or _model is None:
        load_artifacts()
    X = _pydantic_to_row(p)
    Xi = _imputer.transform(X)
    Xs = _scaler.transform(Xi)
    proba = _model.predict_proba(Xs)[0]
    pred = int(np.argmax(proba))
    return pred, proba


def format_result(pred: int, proba: np.ndarray) -> dict:
    """格式化为API响应"""
    return {
        "label_id": pred,
        "label_cn": CLASS_NAMES_CN[pred],
        "label_en": CLASS_NAMES_EN[pred],
        "probabilities": {
            CLASS_NAMES_CN[i]: round(float(proba[i]), 6)
            for i in range(len(CLASS_NAMES_CN))
        },
    }
