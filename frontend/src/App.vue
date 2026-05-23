<script setup>
import { reactive, ref, watch, nextTick, onMounted, onBeforeUnmount } from "vue";
import axios from "axios";
import * as echarts from "echarts";

const LABEL_ORDER = ["优秀", "良好", "及格", "不及格"];
const LABEL_COLORS = ["#22c55e", "#3b82f6", "#f59e0b", "#ef4444"];

const loading = ref(false);
const result = ref(null);
const err = ref("");

const form = reactive({
  test_grade: 1,
  gender: 1,
  height_cm: 172,
  weight_kg: 65,
  bmi: 22.0,
  vital_capacity_ml: 4000,
  run_50m_s: 8.0,
  standing_long_jump_cm: 220,
  sit_reach_cm: 10,
  long_run_sec: 260,
  strength_count: 10,
});

const rules = {
  test_grade: [{ required: true, message: "必填", trigger: "blur" }],
  gender: [{ required: true, message: "必填", trigger: "change" }],
  height_cm: [{ required: true, message: "必填", trigger: "blur" }],
  weight_kg: [{ required: true, message: "必填", trigger: "blur" }],
};

const formRef = ref();

async function onSubmit() {
  err.value = "";
  result.value = null;
  try {
    await formRef.value?.validate();
  } catch {
    return;
  }
  loading.value = true;
  try {
    const payload = { ...form };
    const { data } = await axios.post("/api/predict", payload);
    if (data.ok && data.data) {
      result.value = data.data;
    } else {
      err.value = data.error || "预测失败";
    }
  } catch (e) {
    err.value = e.response?.data?.detail || e.message || "请求失败";
  } finally {
    loading.value = false;
  }
}

function tagType(cn) {
  const m = { 优秀: "success", 良好: "", 及格: "warning", 不及格: "danger" };
  return m[cn] || "info";
}

const chartRef = ref(null);
let chartInstance = null;
let chartResizeObserver = null;

function pct(prob) {
  return Math.round((Number(prob) || 0) * 10000) / 100;
}

function liftHex(hex, lift) {
  if (echarts.color && typeof echarts.color.lift === "function") {
    return echarts.color.lift(hex, lift);
  }
  return hex;
}

function normalizeProbabilities(probs = {}) {
  const aliasMap = {
    优秀: ["优秀", "excellent", "Excellent", "A", "best"],
    良好: ["良好", "good", "Good", "B"],
    及格: ["及格", "pass", "Pass", "medium", "Medium", "C"],
    不及格: ["不及格", "poor", "Poor", "D", "bad"],
  };
  const entries = Object.entries(probs);

  const resultMap = {};
  LABEL_ORDER.forEach((label, idx) => {
    const candidates = aliasMap[label] || [label];
    let value;
    for (const key of candidates) {
      if (probs[key] !== undefined && probs[key] !== null) {
        value = probs[key];
        break;
      }
    }
    if (value === undefined && entries[idx]) {
      value = entries[idx][1];
    }
    resultMap[label] = pct(value);
  });

  return resultMap;
}

function buildProbChartOption(res) {
  const probs = normalizeProbabilities(res.probabilities || {});
  const pieData = LABEL_ORDER.map((name, i) => ({
    name,
    value: probs[name],
    itemStyle: {
      color: LABEL_COLORS[i],
      shadowBlur: name === res.label_cn ? 14 : 0,
      shadowColor: "rgba(15, 23, 42, 0.18)",
    },
  }));

  const barSeriesData = LABEL_ORDER.map((name, i) => ({
    value: probs[name],
    itemStyle: {
      color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
        { offset: 0, color: LABEL_COLORS[i] },
        { offset: 1, color: liftHex(LABEL_COLORS[i], 0.22) },
      ]),
      borderRadius: [0, 8, 8, 0],
    },
  }));

  return {
    animationDuration: 780,
    animationEasing: "cubicOut",
    animationDurationUpdate: 900,
    animationEasingUpdate: "quarticOut",
    backgroundColor: "transparent",
    textStyle: {
      fontFamily:
        '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans SC", sans-serif',
      color: "#475569",
    },
    tooltip: {
      trigger: "item",
      backgroundColor: "rgba(255,255,255,0.96)",
      borderColor: "#e2e8f0",
      borderWidth: 1,
      textStyle: { color: "#334155" },
      formatter(params) {
        if (params.seriesType === "pie") {
          return `${params.marker}${params.name}<br/>占比 <b>${params.percent}%</b>（${params.value}%）`;
        }
        if (params.seriesType === "bar") {
          const label = params.name || LABEL_ORDER[params.dataIndex] || "";
          return `${label}<br/>概率 <b>${params.value}%</b>`;
        }
        return "";
      },
    },
    legend: {
      bottom: 4,
      left: "center",
      icon: "circle",
      itemGap: 16,
      textStyle: { color: "#64748b", fontSize: 12 },
    },
    grid: {
      left: "3%",
      right: "8%",
      top: "54%",
      bottom: "14%",
      containLabel: true,
    },
    xAxis: {
      type: "value",
      max: 100,
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: {
        lineStyle: { color: "#e8eef6", type: "dashed" },
      },
      axisLabel: {
        color: "#94a3b8",
        formatter: "{value}%",
      },
    },
    yAxis: {
      type: "category",
      data: LABEL_ORDER,
      inverse: true,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: "#64748b",
        fontWeight: 500,
      },
    },
    series: [
      {
        name: "类别占比",
        type: "pie",
        animationType: "expansion",
        radius: ["36%", "52%"],
        center: ["50%", "28%"],
        padAngle: 2,
        itemStyle: {
          borderRadius: 8,
          borderColor: "#fff",
          borderWidth: 2,
        },
        label: {
          color: "#334155",
          formatter: "{b}\n{d}%",
          lineHeight: 16,
        },
        labelLine: {
          length: 10,
          length2: 8,
          lineStyle: { color: "#cbd5e1" },
        },
        emphasis: {
          scale: true,
          scaleSize: 6,
          itemStyle: {
            shadowBlur: 20,
            shadowColor: "rgba(37, 99, 235, 0.25)",
          },
        },
        data: pieData,
      },
      {
        name: "条形对比",
        type: "bar",
        showInLegend: false,
        barWidth: "58%",
        data: barSeriesData,
        label: {
          show: true,
          position: "right",
          color: "#64748b",
          formatter: "{c}%",
        },
      },
    ],
  };
}

function buildZeroProbResult(res) {
  return {
    ...res,
    probabilities: LABEL_ORDER.reduce((acc, label) => {
      acc[label] = 0;
      return acc;
    }, {}),
  };
}

function disposeChart() {
  if (chartInstance) {
    chartInstance.dispose();
    chartInstance = null;
  }
}

function resizeChart() {
  chartInstance?.resize();
}

async function initOrUpdateChart(res, retry = 0) {
  await nextTick();
  const el = chartRef.value;
  if (!el) {
    if (retry < 10) {
      window.setTimeout(() => {
        initOrUpdateChart(res, retry + 1);
      }, 80);
    }
    return;
  }

  const width = el.clientWidth;
  const height = el.clientHeight;
  if ((width === 0 || height === 0) && retry < 6) {
    window.setTimeout(() => {
      initOrUpdateChart(res, retry + 1);
    }, 80);
    return;
  }

  if (!chartInstance) {
    chartInstance = echarts.init(el, null, { renderer: "canvas" });
  }
  const startRes = buildZeroProbResult(res);
  chartInstance.setOption(buildProbChartOption(startRes), true);
  window.requestAnimationFrame(() => {
    chartInstance?.setOption(buildProbChartOption(res), false);
  });
  resizeChart();
}

watch(
  result,
  async (r) => {
    if (!r) {
      disposeChart();
      return;
    }
    await initOrUpdateChart(r);
  },
  { flush: "post" }
);

watch(
  chartRef,
  async (el) => {
    if (!el || !result.value) return;
    await initOrUpdateChart(result.value);
    if (chartResizeObserver) {
      chartResizeObserver.observe(el);
    }
  },
  { flush: "post" }
);

function onWinResize() {
  resizeChart();
}

onMounted(() => {
  window.addEventListener("resize", onWinResize);
  if (typeof ResizeObserver !== "undefined") {
    chartResizeObserver = new ResizeObserver(() => resizeChart());
    if (chartRef.value) {
      chartResizeObserver.observe(chartRef.value);
    }
  }
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", onWinResize);
  chartResizeObserver?.disconnect?.();
  chartResizeObserver = null;
  disposeChart();
});
</script>

<template>
  <el-container class="page">
    <div class="bg-orb orb-1"></div>
    <div class="bg-orb orb-2"></div>
    <el-main class="main">
      <section class="hero">
        <div class="hero-content">
          <el-tag type="primary" effect="dark" round class="hero-tag">AI 体测评估系统</el-tag>
          <h1>大学生体质健康分类</h1>
          <p>填写体测指标后，系统将调用 LightGBM 模型预测健康等级（优秀 / 良好 / 及格 / 不及格）</p>
        </div>
      </section>

      <el-row :gutter="20" class="content-row">
        <el-col :xs="24" :lg="15">
          <el-card class="panel-card float-in delay-1" shadow="never">
            <template #header>
              <div class="card-header">
                <span>体测数据录入</span>
                <el-tag size="small" effect="plain">共 11 项指标（论文表3.1）</el-tag>
              </div>
            </template>
            <el-form ref="formRef" :model="form" :rules="rules" label-width="130px" label-position="right" class="data-form">
              <el-form-item label="测试年级" prop="test_grade">
                <el-input-number v-model="form.test_grade" :min="1" :max="4" />
                <span class="field-hint">1-4（大一至大四）</span>
              </el-form-item>
              <el-form-item label="性别" prop="gender">
                <el-radio-group v-model="form.gender">
                  <el-radio :label="1">男</el-radio>
                  <el-radio :label="2">女</el-radio>
                </el-radio-group>
              </el-form-item>
              <el-form-item label="身高 (cm)" prop="height_cm">
                <el-input-number v-model="form.height_cm" :min="120" :max="220" :step="0.1" />
              </el-form-item>
              <el-form-item label="体重 (kg)" prop="weight_kg">
                <el-input-number v-model="form.weight_kg" :min="30" :max="150" :step="0.1" />
              </el-form-item>
              <el-form-item label="BMI" prop="bmi">
                <el-input-number v-model="form.bmi" :min="14" :max="40" :step="0.01" />
                <span class="field-hint">BMI = 体重/身高²</span>
              </el-form-item>
              <el-form-item label="肺活量 (ml)" prop="vital_capacity_ml">
                <el-input-number v-model="form.vital_capacity_ml" :min="1000" :max="8000" />
              </el-form-item>
              <el-form-item label="50米跑 (秒)" prop="run_50m_s">
                <el-input-number v-model="form.run_50m_s" :min="5" :max="15" :step="0.1" />
              </el-form-item>
              <el-form-item label="立定跳远 (cm)" prop="standing_long_jump_cm">
                <el-input-number v-model="form.standing_long_jump_cm" :min="50" :max="300" />
              </el-form-item>
              <el-form-item label="坐位体前屈 (cm)" prop="sit_reach_cm">
                <el-input-number v-model="form.sit_reach_cm" :min="-20" :max="40" :step="0.1" />
              </el-form-item>
              <el-form-item label="长跑秒数" prop="long_run_sec">
                <el-tooltip content="男生1000米 / 女生800米" placement="top">
                  <el-input-number v-model="form.long_run_sec" :min="0" :max="20000" />
                </el-tooltip>
              </el-form-item>
              <el-form-item label="引体/仰卧个数" prop="strength_count">
                <el-input-number v-model="form.strength_count" :min="0" :max="200" />
                <span class="field-hint">男引体向上 / 女仰卧起坐</span>
              </el-form-item>
              <el-form-item class="form-actions">
                <el-button type="primary" size="large" :loading="loading" @click="onSubmit">提交预测</el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>
        <el-col :xs="24" :lg="9">
          <el-card class="panel-card result-card float-in delay-2" shadow="never">
            <template #header>
              <div class="card-header">
                <span>预测结果</span>
                <el-tag type="success" effect="light">实时展示</el-tag>
              </div>
            </template>
            <transition name="fade-up" mode="out-in">
              <el-alert v-if="err" key="err" :title="err" type="error" show-icon :closable="false" />
              <div v-else-if="!result" key="empty" class="placeholder">填写左侧表单并提交</div>
              <div v-else key="result" class="result-block">
                <div class="grade">
                  健康等级：
                  <el-tag :type="tagType(result.label_cn)" size="large" effect="dark">
                    {{ result.label_cn }}
                  </el-tag>
                  <span class="en">（{{ result.label_en }}）</span>
                </div>
                <el-divider />
                <p class="prob-title">各类别概率分布</p>
                <p class="prob-hint">环形图为占比，条形图为各类别概率对比（ECharts）</p>
                <div ref="chartRef" class="prob-chart" aria-label="各类别预测概率图表" />
                <p class="prob-fallback">
                  若图表未显示，请先执行 <code>npm install</code> 安装依赖后刷新页面。
                </p>
              </div>
            </transition>
          </el-card>
        </el-col>
      </el-row>

      <footer class="footer">版权所有 &copy; 韩艺塔<br>基于 LightGBM · FastAPI · Vue3 · Element Plus</footer>
    </el-main>
  </el-container>
</template>

<style scoped>
.page {
  position: relative;
  overflow: hidden;
  min-height: 100vh;
  background: radial-gradient(circle at 0% 0%, #eaf2ff 0%, #f7f9fc 35%, #f3f5f8 100%);
}

.bg-orb {
  position: absolute;
  border-radius: 999px;
  filter: blur(2px);
  opacity: 0.55;
  pointer-events: none;
  z-index: 0;
  animation: drift 10s ease-in-out infinite;
}

.orb-1 {
  width: 240px;
  height: 240px;
  right: -70px;
  top: 70px;
  background: radial-gradient(circle, rgba(37, 99, 235, 0.35), rgba(37, 99, 235, 0.08));
}

.orb-2 {
  width: 180px;
  height: 180px;
  left: -60px;
  bottom: 30px;
  background: radial-gradient(circle, rgba(16, 185, 129, 0.25), rgba(16, 185, 129, 0.05));
  animation-delay: 1.2s;
}

.main {
  position: relative;
  z-index: 1;
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px 16px 28px;
}

.hero {
  border-radius: 20px;
  padding: 24px 28px;
  margin-bottom: 18px;
  background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 48%, #3b82f6 100%);
  color: #fff;
  box-shadow: 0 18px 44px rgba(37, 99, 235, 0.25);
}

.hero-content h1 {
  margin: 12px 0 10px;
  font-size: 30px;
  line-height: 1.2;
  font-weight: 700;
}

.hero-content p {
  margin: 0;
  color: rgba(255, 255, 255, 0.92);
  max-width: 760px;
  line-height: 1.7;
}

.hero-tag {
  border-color: rgba(255, 255, 255, 0.45);
}

.content-row {
  margin-top: 8px;
}

.panel-card {
  border-radius: 16px;
  border: 1px solid #e8eef6;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
  transition: transform 0.26s ease, box-shadow 0.26s ease;
}

.panel-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.09);
}

.panel-card :deep(.el-card__header) {
  padding: 14px 18px;
  border-bottom: 1px solid #edf1f7;
}

.panel-card :deep(.el-card__body) {
  padding: 18px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-weight: 600;
  color: #1f2d3d;
}

.data-form :deep(.el-form-item) {
  margin-bottom: 18px;
}

.data-form :deep(.el-input-number) {
  width: 100%;
}

.field-hint {
  margin-left: 8px;
  font-size: 12px;
  color: #94a3b8;
}

.form-actions {
  margin-top: 8px;
  margin-bottom: 0;
}

.form-actions :deep(.el-button) {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.form-actions :deep(.el-button:hover) {
  transform: translateY(-1px);
  box-shadow: 0 8px 18px rgba(37, 99, 235, 0.24);
}

.result-card {
  min-height: 100%;
}

.footer {
  text-align: center;
  color: #8a94a6;
  font-size: 13px;
  padding: 22px 8px 6px;
}
.placeholder {
  color: #8a94a6;
  padding: 56px 0;
  text-align: center;
  border: 1px dashed #dce4ef;
  border-radius: 12px;
  background: #fafcff;
}
.result-block {
  padding: 4px 0;
}
.grade {
  font-size: 20px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.en {
  color: #909399;
  font-size: 14px;
}
.prob-title {
  margin: 0 0 6px;
  color: #606266;
  font-weight: 500;
}

.prob-hint {
  margin: 0 0 12px;
  font-size: 12px;
  color: #94a3b8;
  line-height: 1.5;
}

.prob-chart {
  width: 100%;
  min-height: 400px;
  border-radius: 12px;
  background: linear-gradient(180deg, #fafcff 0%, #f4f7fb 100%);
  border: 1px solid #edf1f7;
}

.prob-fallback {
  margin: 10px 0 0;
  font-size: 12px;
  color: #94a3b8;
}

.float-in {
  animation: floatIn 0.5s ease both;
}

.delay-1 {
  animation-delay: 0.04s;
}

.delay-2 {
  animation-delay: 0.12s;
}

.fade-up-enter-active,
.fade-up-leave-active {
  transition: all 0.26s ease;
}

.fade-up-enter-from,
.fade-up-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

@keyframes floatIn {
  from {
    opacity: 0;
    transform: translateY(14px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes drift {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-12px);
  }
}

@media (max-width: 992px) {
  .hero {
    padding: 20px;
    border-radius: 16px;
  }

  .hero-content h1 {
    font-size: 24px;
  }

  .main {
    padding: 14px 12px 24px;
  }
}
</style>
