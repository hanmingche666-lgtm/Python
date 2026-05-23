# -*- coding: utf-8 -*-
"""FastAPI 应用入口"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import HealthResponse, PredictIn, PredictOut
from app.service import format_result, load_artifacts, predict_one


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        load_artifacts()
    except FileNotFoundError:
        pass
    yield


app = FastAPI(
    title="大学生体质健康分类 API",
    version="1.0.0",
    description="基于LightGBM的大学生体质健康四分类预测服务",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=HealthResponse)
def predict(body: PredictIn):
    try:
        pred, proba = predict_one(body)
        data = PredictOut(**format_result(pred, proba))
        return HealthResponse(ok=True, data=data)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
