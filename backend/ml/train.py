# -*- coding: utf-8 -*-
"""
LightGBM 体质健康四分类模型训练脚本。
与论文第3-4章完全一致：
  - 特征体系：表3.1（11维）
  - 数据划分：7:2:1 分层抽样（3.2.2节）
  - 超参数优化：GridSearchCV + 五折交叉验证（3.3节）
  - 对比模型：随机森林、逻辑回归（4.1节）
产物写入 backend/artifacts/
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from ml.config import CLASS_NAMES_CN, FEATURE_COLUMNS
from ml.preprocess import build_features_labels, load_raw_excel


def _multiclass_roc_auc(y_true, y_proba, n_classes: int) -> float:
    """多分类 ROC-AUC（OVR, weighted average）"""
    try:
        from sklearn.preprocessing import label_binarize
        yb = label_binarize(y_true, classes=list(range(n_classes)))
        return roc_auc_score(yb, y_proba, multi_class="ovr", average="weighted")
    except Exception:
        return float("nan")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    art = root / "artifacts"
    art.mkdir(parents=True, exist_ok=True)

    # ============================================================
    # 第2章：数据预处理
    # ============================================================
    print("=" * 60)
    print("第2章：加载与预处理数据")
    print("=" * 60)
    df = load_raw_excel()
    X_df, y = build_features_labels(df)
    X = X_df.values
    total_samples = len(y)
    print(f"预处理后总样本数: {total_samples}")

    # ============================================================
    # 第3.2.2节：7:2:1 分层抽样划分
    # ============================================================
    print("\n" + "=" * 60)
    print("第3.2.2节：7:2:1 分层抽样数据划分")
    print("=" * 60)

    # 先分出测试集 10%
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=0.1, random_state=42, stratify=y
    )
    # 剩余90%中分出验证集（约22.22% → 整体的20%）
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp,
        test_size=2.0 / 9.0,
        random_state=42,
        stratify=y_temp,
    )

    print(f"训练集: {len(X_train)}  验证集: {len(X_val)}  测试集: {len(X_test)}")
    for i, name in enumerate(CLASS_NAMES_CN):
        print(f"  {name}: 训练{sum(y_train==i)}  验证{sum(y_val==i)}  测试{sum(y_test==i)}  "
              f"总计{sum(y_train==i)+sum(y_val==i)+sum(y_test==i)}  "
              f"占比{sum(y_train==i)+sum(y_val==i)+sum(y_test==i)/total_samples*100:.1f}%")

    # 缺失值填补（论文2.2.2节：按性别+测试年级分组均值填补的简化实现）
    imputer = SimpleImputer(strategy="median")
    X_train_i = imputer.fit_transform(X_train)
    X_val_i = imputer.transform(X_val)
    X_test_i = imputer.transform(X_test)

    # 标准化（论文2.2.5节）
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train_i)
    X_val_s = scaler.transform(X_val_i)
    X_test_s = scaler.transform(X_test_i)

    # ============================================================
    # 第3.3节：GridSearchCV 超参数优化
    # ============================================================
    print("\n" + "=" * 60)
    print("第3.3节：GridSearchCV 超参数优化（五折交叉验证）")
    print("=" * 60)

    base = LGBMClassifier(
        objective="multiclass",
        num_class=4,
        random_state=42,
        n_jobs=-1,
        verbose=-1,
    )

    # 论文3.3.3节定义的完整搜索空间
    param_grid = {
        "num_leaves": [31, 63, 127],
        "max_depth": [5, 10, 15, -1],
        "learning_rate": [0.01, 0.05, 0.1],
        "n_estimators": [100, 500, 1000],
        "min_child_samples": [20, 50, 100],
        "feature_fraction": [0.6, 0.8, 1.0],
    }
    total_combos = (
        len(param_grid["num_leaves"]) *
        len(param_grid["max_depth"]) *
        len(param_grid["learning_rate"]) *
        len(param_grid["n_estimators"]) *
        len(param_grid["min_child_samples"]) *
        len(param_grid["feature_fraction"])
    )
    print(f"参数组合总数: {total_combos} × 5折 = {total_combos * 5} 次训练")
    print("开始搜索（可能需要较长时间）...")

    t0 = time.time()
    grid = GridSearchCV(
        base,
        param_grid,
        scoring="f1_weighted",
        cv=5,              # 五折交叉验证（论文3.3.1节）
        n_jobs=-1,
        verbose=1,
    )
    grid.fit(X_train_s, y_train)

    best_lgb = grid.best_estimator_
    elapsed = time.time() - t0
    print(f"\n网格搜索完成，耗时: {elapsed:.1f} 秒")
    print(f"最优交叉验证得分 (F1-weighted): {grid.best_score_:.4f}")
    print(f"最优参数: {grid.best_params_}")

    # ============================================================
    # 第4章：模型性能验证
    # ============================================================
    print("\n" + "=" * 60)
    print("第4章：模型分类性能验证")
    print("=" * 60)

    # --- LightGBM ---
    y_pred_lgb = best_lgb.predict(X_test_s)
    proba_lgb = best_lgb.predict_proba(X_test_s)

    def pack_metrics(name: str, y_pred, y_proba) -> dict:
        return {
            "model": name,
            "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
            "precision_weighted": round(float(precision_score(
                y_test, y_pred, average="weighted", zero_division=0)), 4),
            "recall_weighted": round(float(recall_score(
                y_test, y_pred, average="weighted", zero_division=0)), 4),
            "f1_weighted": round(float(f1_score(
                y_test, y_pred, average="weighted", zero_division=0)), 4),
            "f1_macro": round(float(f1_score(
                y_test, y_pred, average="macro", zero_division=0)), 4),
            "roc_auc_ovr_weighted": round(
                float(_multiclass_roc_auc(y_test, y_proba, 4)), 4),
        }

    metrics = [pack_metrics("LightGBM", y_pred_lgb, proba_lgb)]

    # --- 随机森林对比 ---
    rf = RandomForestClassifier(
        n_estimators=200, max_depth=20, random_state=42,
        n_jobs=-1, class_weight="balanced_subsample",
    )
    rf.fit(X_train_s, y_train)
    proba_rf = rf.predict_proba(X_test_s)
    metrics.append(pack_metrics("RandomForest", rf.predict(X_test_s), proba_rf))

    # --- 逻辑回归对比 ---
    pipe_lr = Pipeline([
        ("scaler", StandardScaler()),  # LR需额外标准化
        ("clf", LogisticRegression(
            max_iter=2000, multi_class="multinomial",
            random_state=42, n_jobs=-1,
        )),
    ])
    pipe_lr.fit(X_train_s, y_train)
    proba_lr = pipe_lr.predict_proba(X_test_s)
    metrics.append(pack_metrics("LogisticRegression",
                   pipe_lr.predict(X_test_s), proba_lr))

    # --- 分类报告 ---
    report = classification_report(
        y_test, y_pred_lgb,
        target_names=CLASS_NAMES_CN,
        digits=4, zero_division=0,
    )
    print("\nLightGBM 分类报告（测试集）:")
    print(report)

    print("\n模型性能对比（表4.1格式）:")
    print(f"{'模型':<20} {'Accuracy':>8} {'Precision':>10} {'Recall':>10} "
          f"{'F1(w)':>8} {'F1(macro)':>10} {'ROC-AUC':>8}")
    print("-" * 76)
    for m in metrics:
        print(f"{m['model']:<20} {m['accuracy']:>8.4f} {m['precision_weighted']:>10.4f} "
              f"{m['recall_weighted']:>10.4f} {m['f1_weighted']:>8.4f} "
              f"{m['f1_macro']:>10.4f} {m['roc_auc_ovr_weighted']:>8.4f}")

    # ============================================================
    # 保存产物
    # ============================================================
    print("\n" + "=" * 60)
    print("保存模型产物")
    print("=" * 60)

    # 用训练集+验证集重新训练最优模型（论文3.3.3节末尾）
    X_train_full = np.vstack([X_train_s, X_val_s])
    y_train_full = np.concatenate([y_train, y_val])
    final_model = LGBMClassifier(
        objective="multiclass", num_class=4,
        random_state=42, n_jobs=-1, verbose=-1,
        **grid.best_params_,
    )
    final_model.fit(X_train_full, y_train_full)

    # 保存
    joblib.dump(imputer, art / "imputer.joblib")
    joblib.dump(scaler, art / "scaler.joblib")
    joblib.dump(final_model, art / "lgb_model.joblib")

    bp = grid.best_params_
    best_params_table = {
        "num_leaves": bp.get("num_leaves"),
        "max_depth": bp.get("max_depth"),
        "learning_rate": bp.get("learning_rate"),
        "n_estimators": bp.get("n_estimators"),
        "min_child_samples": bp.get("min_child_samples"),
        "feature_fraction": bp.get("feature_fraction"),
        "默认值参考": {
            "num_leaves": 31, "max_depth": -1, "learning_rate": 0.1,
            "n_estimators": 100, "min_child_samples": 20, "feature_fraction": 1.0,
        },
    }

    meta = {
        "feature_columns": FEATURE_COLUMNS,
        "class_names_cn": CLASS_NAMES_CN,
        "grid_param_space": {
            "num_leaves": [31, 63, 127],
            "max_depth": [5, 10, 15, -1],
            "learning_rate": [0.01, 0.05, 0.1],
            "n_estimators": [100, 500, 1000],
            "min_child_samples": [20, 50, 100],
            "feature_fraction": [0.6, 0.8, 1.0],
        },
        "grid_best_params": best_params_table,
        "grid_best_cv_score": round(float(grid.best_score_), 4),
        "cv_folds": 5,
        "classification_report_lgb": report,
        "data_split": {
            "train": len(X_train),
            "val": len(X_val),
            "test": len(X_test),
            "total": total_samples,
            "ratio": "7:2:1",
        },
        "metrics_comparison": metrics,
    }
    (art / "model_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (art / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("产物已保存至:", art)
    print("  - imputer.joblib, scaler.joblib: 预处理器")
    print("  - lgb_model.joblib: 最优LightGBM模型")
    print("  - metrics.json: 三模型性能对比")
    print("  - model_meta.json: 完整元信息与分类报告")


if __name__ == "__main__":
    main()
