<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { RefreshCw, Search, Sparkles } from 'lucide-vue-next'
import RiskBadge from '../components/RiskBadge.vue'
import { api } from '../services/api'

const loading = ref(true)
const error = ref('')
const payload = ref({ items: [], filters: { categories: [], health: [] }, total: 0 })
const activePrediction = ref(null)
const filters = reactive({
  category: '',
  health: '',
  search: '',
  limit: 36,
  offset: 0,
})

async function loadProducts() {
  try {
    loading.value = true
    error.value = ''
    payload.value = await api.products(filters)
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function runStock(product) {
  activePrediction.value = await api.runStockPrediction(product.product_id)
}

function stockPercent(product) {
  return Math.min(100, Math.round((product.current_stock / product.optimal_stock) * 100))
}

watch(() => [filters.category, filters.health], () => {
  filters.offset = 0
  loadProducts()
})

onMounted(loadProducts)
</script>

<template>
  <div class="page-stack">
    <header class="page-header">
      <div>
        <span class="eyebrow">Inventory network</span>
        <h1>Stock Health</h1>
        <p>Current stock, reorder thresholds, supplier reliability, and days-to-stockout estimates.</p>
      </div>
      <button class="command-button" type="button" @click="loadProducts">
        <RefreshCw :size="17" />
        Refresh
      </button>
    </header>

    <section class="toolbar">
      <label class="search-field">
        <Search :size="17" />
        <input v-model="filters.search" type="search" placeholder="Search SKU or product" @keydown.enter="loadProducts" />
      </label>
      <label>
        <select v-model="filters.category">
          <option value="">All categories</option>
          <option v-for="category in payload.filters.categories" :key="category" :value="category">{{ category }}</option>
        </select>
      </label>
      <label>
        <select v-model="filters.health">
          <option value="">All health states</option>
          <option value="critical">critical</option>
          <option value="watch">watch</option>
          <option value="healthy">healthy</option>
        </select>
      </label>
      <button class="command-button subtle" type="button" @click="loadProducts">
        <Search :size="16" />
        Search
      </button>
    </section>

    <div v-if="error" class="error-banner">{{ error }}</div>
    <div v-if="loading" class="loading-band">Loading inventory...</div>

    <section v-if="activePrediction" class="panel live-result">
      <RiskBadge :risk="activePrediction.risk_level" />
      <strong>{{ activePrediction.model_name }}</strong>
      <p>{{ activePrediction.explanation }} Average daily demand is {{ activePrediction.avg_daily_demand }} units.</p>
    </section>

    <section class="inventory-grid">
      <article v-for="product in payload.items" :key="product.product_id" class="product-card" :class="`health-${product.health}`">
        <div class="product-card-top">
          <div>
            <span class="field-label">{{ product.sku }}</span>
            <h2>{{ product.name }}</h2>
          </div>
          <RiskBadge :risk="product.shortage_prediction.risk_level" />
        </div>
        <div class="stock-meter" aria-hidden="true">
          <span :style="{ width: `${stockPercent(product)}%` }"></span>
        </div>
        <div class="stock-values">
          <div>
            <span class="field-label">Current</span>
            <strong>{{ product.current_stock.toLocaleString('en-IN') }}</strong>
          </div>
          <div>
            <span class="field-label">Reorder</span>
            <strong>{{ product.reorder_threshold.toLocaleString('en-IN') }}</strong>
          </div>
          <div>
            <span class="field-label">Stockout</span>
            <strong>{{ product.shortage_prediction.days_to_stockout }} days</strong>
          </div>
        </div>
        <p class="supplier-line">{{ product.supplier_name }} | {{ product.supplier_city }} | {{ Math.round(product.supplier_reliability * 100) }}%</p>
        <button class="command-button subtle full-width" type="button" @click="runStock(product)">
          <Sparkles :size="16" />
          Run Stock Model
        </button>
      </article>
    </section>
  </div>
</template>
