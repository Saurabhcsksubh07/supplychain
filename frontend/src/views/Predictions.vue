<script setup>
import { computed, onMounted, ref } from 'vue'
import { BrainCircuit, RefreshCw } from 'lucide-vue-next'
import ChartPanel from '../components/ChartPanel.vue'
import KpiCard from '../components/KpiCard.vue'
import RiskBadge from '../components/RiskBadge.vue'
import { api } from '../services/api'

const loading = ref(true)
const error = ref('')
const data = ref(null)

async function loadPredictions() {
  try {
    loading.value = true
    error.value = ''
    data.value = await api.predictions()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

const riskChart = computed(() => ({
  labels: data.value?.risk_distribution?.map((row) => row.risk) || [],
  datasets: [
    {
      label: 'Predictions',
      data: data.value?.risk_distribution?.map((row) => row.count) || [],
      backgroundColor: ['#dc2626', '#f59e0b', '#16a34a'],
    },
  ],
}))

const accuracyChart = computed(() => ({
  labels: data.value?.accuracy_history?.map((row) => row.month) || [],
  datasets: [
    {
      label: 'Delay',
      data: data.value?.accuracy_history?.map((row) => row.delay * 100) || [],
      borderColor: '#2563eb',
      tension: 0.3,
    },
    {
      label: 'Stock',
      data: data.value?.accuracy_history?.map((row) => row.stock * 100) || [],
      borderColor: '#0f766e',
      tension: 0.3,
    },
    {
      label: 'Cost',
      data: data.value?.accuracy_history?.map((row) => row.cost * 100) || [],
      borderColor: '#b45309',
      tension: 0.3,
    },
  ],
}))

onMounted(loadPredictions)
</script>

<template>
  <div class="page-stack">
    <header class="page-header">
      <div>
        <span class="eyebrow">Predictive intelligence</span>
        <h1>Model Performance</h1>
        <p>Accuracy, risk mix, feature importance, and recent prediction activity.</p>
      </div>
      <button class="command-button" type="button" @click="loadPredictions">
        <RefreshCw :size="17" />
        Refresh
      </button>
    </header>

    <div v-if="error" class="error-banner">{{ error }}</div>
    <div v-if="loading" class="loading-band">Loading model data...</div>

    <template v-if="data">
      <section class="kpi-grid">
        <KpiCard
          v-for="metric in data.metrics"
          :key="metric.model"
          :label="metric.model"
          :value="`${Math.round(metric.accuracy * 100)}%`"
          :detail="`${metric.algorithm} | ${metric.key_score}`"
          tone="blue"
          :icon="BrainCircuit"
        />
      </section>

      <section class="dashboard-grid">
        <ChartPanel title="Risk Distribution" type="bar" :data="riskChart" />
        <ChartPanel title="Accuracy History" type="line" :data="accuracyChart" :options="{ scales: { y: { min: 70, max: 90 } } }" />
      </section>

      <section class="panel">
        <div class="section-heading">
          <h2>Feature Importance</h2>
        </div>
        <div class="importance-grid">
          <article v-for="(features, model) in data.feature_importance" :key="model">
            <h3>{{ model }}</h3>
            <div v-for="feature in features" :key="feature.feature" class="importance-row">
              <span>{{ feature.feature }}</span>
              <div class="importance-meter"><span :style="{ width: `${Math.round(feature.importance * 100)}%` }"></span></div>
              <strong>{{ Math.round(feature.importance * 100) }}%</strong>
            </div>
          </article>
        </div>
      </section>

      <section class="panel">
        <div class="section-heading">
          <h2>Latest Predictions</h2>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Model</th>
                <th>Entity</th>
                <th>Risk</th>
                <th>Score</th>
                <th>Confidence</th>
                <th>Explanation</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in data.latest" :key="row.prediction_id">
                <td>{{ row.model_name }}</td>
                <td>{{ row.entity_type }} #{{ row.entity_id }}</td>
                <td><RiskBadge :risk="row.risk_level" /></td>
                <td>{{ row.score }}</td>
                <td>{{ Math.round(row.confidence * 100) }}%</td>
                <td>{{ row.explanation }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </div>
</template>
