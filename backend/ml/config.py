# -*- coding: utf-8 -*-
"""数据集列名与特征配置（与论文表3.1一致）"""

DATA_PATH = "data.xlsx"

# 论文表3.1 模型输入特征体系 —— 11维核心特征
# 涵盖基础属性、形态指标、运动素质三个维度
FEATURE_COLUMNS = [
    "测试年级",       # 类别型 1-4（大一至大四）
    "性别",           # 二分类 1=男 2=女
    "身高cm",         # 数值型 120-220cm
    "体重kg",         # 数值型 30-150kg
    "BMI",            # 数值型 BMI=W/H²
    "肺活量ml",       # 数值型 1000-8000ml
    "50M跑（s）",     # 数值型 5-15s
    "立定跳远cm",     # 数值型 50-300cm
    "坐位体前屈cm",   # 数值型 -20-40cm
    "长跑秒数（s）",  # 数值型 男1000米/女800米
    "引体仰卧个数",   # 数值型 男引体向上/女仰卧起坐
]

LABEL_SCORE_COL = "总分"

# 论文：优秀、良好、及格、不及格 四个等级
CLASS_NAMES_CN = ["优秀", "良好", "及格", "不及格"]
CLASS_NAMES_EN = ["Excellent", "Good", "Pass", "Fail"]


def score_to_label(score: float) -> int:
    """根据体质健康综合得分映射为四分类标签（论文3.2.1节标签编码）"""
    if score >= 85:
        return 0  # 优秀
    if score >= 70:
        return 1  # 良好
    if score >= 60:
        return 2  # 及格
    return 3      # 不及格
