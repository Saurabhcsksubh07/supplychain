<script setup>
import { Chart, registerables } from 'chart.js'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

Chart.register(...registerables)

const props = defineProps({
  title: { type: String, required: true },
  type: { type: String, default: 'bar' },
  data: { type: Object, required: true },
  options: { type: Object, default: () => ({}) },
})

const canvas = ref(null)
let chart = null

function renderChart() {
  if (!canvas.value) return
  if (chart) chart.destroy()
  chart = new Chart(canvas.value, {
    type: props.type,
    data: props.data,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { boxWidth: 10, usePointStyle: true } },
        tooltip: { mode: 'index', intersect: false },
      },
      scales: props.type === 'doughnut' ? {} : { y: { beginAtZero: true, grid: { color: '#e5e7eb' } } },
      ...props.options,
    },
  })
}

onMounted(renderChart)
onBeforeUnmount(() => chart?.destroy())
watch(() => props.data, renderChart, { deep: true })
</script>

<template>
  <section class="panel chart-panel">
    <div class="section-heading">
      <h2>{{ title }}</h2>
    </div>
    <div class="chart-frame">
      <canvas ref="canvas"></canvas>
    </div>
  </section>
</template>
