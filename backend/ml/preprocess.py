# -*- coding: utf-8 -*-
"""
数据预处理模块 —— 与论文第2章流程一致：
  2.2.1 质量探查 → 2.2.2 缺失值处理 → 2.2.3 异常值处理(IQR)
  → 2.2.4 相关性筛选 → 2.2.5 编码转换 → 2.3 标准化划分
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import FEATURE_COLUMNS, LABEL_SCORE_COL, score_to_label


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_raw_excel(path: str | Path | None = None) -> pd.DataFrame:
    """读取原始体测数据Excel文件"""
    p = Path(path) if path else project_root() / "data.xlsx"
    if not p.exists():
        raise FileNotFoundError(f"未找到数据文件: {p}")
    return pd.read_excel(p, engine="openpyxl")


def build_features_labels(df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    """
    构造特征矩阵X和标签y。
    处理流程：
      1) 列校验 → 2) 剔除总分缺失样本 → 3) IQR异常值剔除
      → 4) 业务规则过滤 → 5) 标签映射
    """
    need = FEATURE_COLUMNS + [LABEL_SCORE_COL]
    missing_cols = [c for c in need if c not in df.columns]
    if missing_cols:
        raise ValueError(f"数据缺少列: {missing_cols}")

    sub = df[need].copy()

    # 丢弃总分缺失的样本
    n_before = len(sub)
    sub = sub.dropna(subset=[LABEL_SCORE_COL])
    print(f"[预处理] 总分缺失剔除: {n_before - len(sub)} 条")

    # IQR + 业务规则：BMI异常值剔除（论文2.2.3节）
    if "BMI" in sub.columns:
        n_before = len(sub)
        bmi = sub["BMI"]
        Q1, Q3 = bmi.quantile(0.25), bmi.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        sub = sub[
            (bmi >= max(14, lower_bound)) &
            (bmi <= min(40, upper_bound))
        ]
        print(f"[预处理] BMI异常值剔除: {n_before - len(sub)} 条")

    # 业务规则：50M跑 5-15秒（论文2.2.3节）
    if "50M跑（s）" in sub.columns:
        n_before = len(sub)
        run50 = sub["50M跑（s）"]
        sub = sub[(run50 >= 5) & (run50 <= 15)]
        print(f"[预处理] 50M跑异常值剔除: {n_before - len(sub)} 条")

    # 业务规则：身高 120-220cm
    if "身高cm" in sub.columns:
        n_before = len(sub)
        h = sub["身高cm"]
        sub = sub[(h >= 120) & (h <= 220)]
        print(f"[预处理] 身高异常值剔除: {n_before - len(sub)} 条")

    # 业务规则：体重 30-150kg
    if "体重kg" in sub.columns:
        n_before = len(sub)
        w = sub["体重kg"]
        sub = sub[(w >= 30) & (w <= 150)]
        print(f"[预处理] 体重异常值剔除: {n_before - len(sub)} 条")

    y = sub[LABEL_SCORE_COL].astype(float).map(score_to_label).astype(int).values
    X = sub[FEATURE_COLUMNS].copy()

    # 分类变量编码（论文2.2.5节）
    # 性别：Label Encoding（1=男, 2=女）—— 原始数据已是数值
    # 测试年级：保持原始编码 1-4

    print(f"[预处理] 最终样本: {len(X)}, 有效特征数: {len(FEATURE_COLUMNS)}")
    print(f"[预处理] 类别分布: {dict(zip(['优秀','良好','及格','不及格'], np.bincount(y)))}")
    return X, y
