# -*- coding: utf-8 -*-
"""Pydantic 接口模型 —— 与论文表3.1一致（11维特征）"""
from pydantic import BaseModel, Field


class PredictIn(BaseModel):
    """论文表3.1 模型输入特征体系"""
    test_grade: int = Field(
        ..., ge=1, le=4, description="测试年级 1-4（大一至大四）")
    gender: int = Field(
        ..., ge=1, le=2, description="性别 1=男 2=女")
    height_cm: float = Field(
        ..., gt=0, le=300, description="身高 cm（范围: 120-220）")
    weight_kg: float = Field(
        ..., gt=0, le=300, description="体重 kg（范围: 30-150）")
    bmi: float = Field(
        ..., gt=0, le=80, description="BMI（由身高/体重计算: BMI=W/H²）")
    vital_capacity_ml: float = Field(
        ..., ge=0, description="肺活量 ml（范围: 1000-8000）")
    run_50m_s: float = Field(
        ..., gt=0, le=60, description="50M跑 秒（范围: 5-15）")
    standing_long_jump_cm: float = Field(
        ..., ge=0, description="立定跳远 cm（范围: 50-300）")
    sit_reach_cm: float = Field(
        ..., ge=-50, le=50, description="坐位体前屈 cm（范围: -20~40）")
    long_run_sec: float = Field(
        ..., ge=0, le=20000, description="长跑秒数（男1000米/女800米）")
    strength_count: float = Field(
        ..., ge=0, description="引体向上/仰卧起坐个数")


class PredictOut(BaseModel):
    label_id: int
    label_cn: str
    label_en: str
    probabilities: dict[str, float]


class HealthResponse(BaseModel):
    ok: bool = True
    data: PredictOut | None = None
    error: str | None = None
