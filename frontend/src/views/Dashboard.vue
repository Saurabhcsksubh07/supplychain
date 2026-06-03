<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { AlertTriangle, BarChart3, Boxes, BrainCircuit, RefreshCw, Truck } from 'lucide-vue-next'
import AlertList from '../components/AlertList.vue'
import ChartPanel from '../components/ChartPanel.vue'
import KpiCard from '../components/KpiCard.vue'
import RiskBadge from '../components/RiskBadge.vue'
import { api } from '../services/api'

const loading = ref(true)
const error = ref('')
const data = ref(null)
let refreshTimer = null

async function loadDashboard() {
  try {
    error.value = ''
    data.value = await api.dashboard()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function resolveAlert(id) {
  await api.resolveAlert(id)
  await loadDashboard()
}

const statusChart = computed(() => ({
  labels: data.value?.status_distribution?.map((row) => row.status) || [],
  datasets: [
    {
      data: data.value?.status_distribution?.map((row) => row.count) || [],
      backgroundColor: ['#2563eb', '#f59e0b', '#dc2626', '#16a34a', '#64748b'],
      borderWidth: 0,
    },
  ],
}))

const stockTrendChart = computed(() => ({
  labels: data.value?.stock_trend?.map((row) => row.date.slice(5)) || [],
  datasets: [
    {
      label: 'Stock movement',
      data: data.value?.stock_trend?.map((row) => row.movement) || [],
      borderColor: '#0f766e',
      backgroundColor: 'rgba(15, 118, 110, 0.12)',
      fill: true,
      tension: 0.35,
    },
  ],
}))

const categoryChart = computed(() => ({
  labels: data.value?.category_stock?.map((row) => row.category) || [],
  datasets: [
    {
      label: 'Average stock',
      data: data.value?.category_stock?.map((row) => row.avg_stock) || [],
      backgroundColor: '#2563eb',
    },
    {
      label: 'Average threshold',
      data: data.value?.category_stock?.map((row) => row.avg_threshold) || [],
      backgroundColor: '#f59e0b',
    },
  ],
}))

onMounted(() => {
  loadDashboard()
  refreshTimer = window.setInterval(loadDashboard, 30_000)
})

onBeforeUnmount(() => window.clearInterval(refreshTimer))
</script>

<template>
  <div class="page-stack">
    <header class="page-header">
      <div>
        <span class="eyebrow">Indian logistics network</span>
        <h1>Supply Chain Command Centre</h1>
        <p>{{ data?.report_context?.stack || 'FastAPI, Vue.js, and predictive intelligence' }}</p>
      </div>
      <button class="command-button" type="button" @click="loadDashboard">
        <RefreshCw :size="17" />
        Refresh
      </button>
    </header>

    <div v-if="error" class="error-banner">{{ error }}</div>
    <div v-if="loading" class="loading-band">Loading operations data...</div>

    <template v-if="data">
      <section class="kpi-grid" aria-label="Supply chain KPIs">
        <KpiCard label="Active Shipments" :value="data.kpis.active_shipments" detail="Pending, in transit, delayed" tone="blue" :icon="Truck" />
        <KpiCard label="High Risk Shipments" :value="data.kpis.high_risk_shipments" detail="ML risk above threshold" tone="red" :icon="AlertTriangle" />
        <KpiCard label="Low Stock Products" :value="data.kpis.low_stock_products" detail="Below reorder threshold" tone="amber" :icon="Boxes" />
        <KpiCard label="Model Accuracy" :value="`${Math.round(data.kpis.average_model_accuracy * 100)}%`" :detail="data.kpis.seeded_records + ' seeded records'" tone="green" :icon="BrainCircuit" />
      </section>

      <section class="dashboard-grid">
        <ChartPanel title="Shipment Status" type="doughnut" :data="statusChart" />
        <ChartPanel title="30-Day Stock Movement" type="line" :data="stockTrendChart" />
      </section>

      <section class="dashboard-grid two-one">
        <ChartPanel title="Category Stock vs Threshold" type="bar" :data="categoryChart" />
        <AlertList :alerts="data.alerts" @resolve="resolveAlert" />
      </section>

      <section class="panel">
        <div class="section-heading">
          <h2>Route Risk Snapshot</h2>
          <BarChart3 :size="19" />
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Route</th>
                <th>Active</th>
                <th>Delayed</th>
                <th>Delay Rate</th>
                <th>Estimated Cost</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="route in data.route_risks" :key="route.route">
                <td>{{ route.route }}</td>
                <td>{{ route.active }}</td>
                <td>{{ route.delayed }}</td>
                <td><RiskBadge :risk="route.delay_rate > 0.45 ? 'HIGH' : route.delay_rate > 0.2 ? 'MEDIUM' : 'LOW'" /></td>
                <td>Rs {{ route.estimated_cost.toLocaleString('en-IN') }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </div>
</template>
