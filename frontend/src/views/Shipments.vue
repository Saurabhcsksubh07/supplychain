<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { Filter, RefreshCw, Search, Sparkles, X } from 'lucide-vue-next'
import RiskBadge from '../components/RiskBadge.vue'
import { api } from '../services/api'

const loading = ref(true)
const error = ref('')
const payload = ref({ items: [], filters: { statuses: [], cities: [], carriers: [] }, total: 0 })
const selected = ref(null)
const livePrediction = ref(null)
const filters = reactive({
  status: '',
  city: '',
  carrier_id: '',
  search: '',
  limit: 25,
  offset: 0,
})

async function loadShipments() {
  try {
    loading.value = true
    error.value = ''
    payload.value = await api.shipments(filters)
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function openDetails(row) {
  selected.value = row
  livePrediction.value = null
}

async function runPrediction(kind) {
  if (!selected.value) return
  livePrediction.value =
    kind === 'delay'
      ? await api.runDelayPrediction(selected.value.shipment_id)
      : await api.runCostPrediction(selected.value.shipment_id)
}

async function updateStatus(row, status) {
  const updated = await api.updateShipment(row.shipment_id, { status })
  Object.assign(row, updated)
}

watch(() => [filters.status, filters.city, filters.carrier_id], () => {
  filters.offset = 0
  loadShipments()
})

onMounted(loadShipments)
</script>

<template>
  <div class="page-stack">
    <header class="page-header">
      <div>
        <span class="eyebrow">Shipment operations</span>
        <h1>Consignment Control</h1>
        <p>Searchable route, carrier, status, and prediction detail for live consignments.</p>
      </div>
      <button class="command-button" type="button" @click="loadShipments">
        <RefreshCw :size="17" />
        Refresh
      </button>
    </header>

    <section class="toolbar">
      <label class="search-field">
        <Search :size="17" />
        <input v-model="filters.search" type="search" placeholder="Search SKU or product" @keydown.enter="loadShipments" />
      </label>
      <label>
        <Filter :size="16" />
        <select v-model="filters.status">
          <option value="">All statuses</option>
          <option v-for="status in payload.filters.statuses" :key="status" :value="status">{{ status.replace('_', ' ') }}</option>
        </select>
      </label>
      <label>
        <select v-model="filters.city">
          <option value="">All cities</option>
          <option v-for="city in payload.filters.cities" :key="city" :value="city">{{ city }}</option>
        </select>
      </label>
      <label>
        <select v-model="filters.carrier_id">
          <option value="">All carriers</option>
          <option v-for="carrier in payload.filters.carriers" :key="carrier.carrier_id" :value="carrier.carrier_id">
            {{ carrier.name }}
          </option>
        </select>
      </label>
      <button class="command-button subtle" type="button" @click="loadShipments">
        <Search :size="16" />
        Search
      </button>
    </section>

    <div v-if="error" class="error-banner">{{ error }}</div>

    <section class="panel">
      <div class="section-heading">
        <h2>{{ payload.total.toLocaleString('en-IN') }} Shipments</h2>
      </div>
      <div class="table-wrap">
        <table class="shipment-table">
          <thead>
            <tr>
              <th>Shipment</th>
              <th>Route</th>
              <th>Carrier</th>
              <th>Status</th>
              <th>Delay Risk</th>
              <th>Cost Risk</th>
              <th>ETA</th>
              <th>Cost</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="9">Loading shipments...</td>
            </tr>
            <tr v-for="row in payload.items" :key="row.shipment_id">
              <td>
                <strong>#{{ row.shipment_id }}</strong>
                <span>{{ row.sku }}</span>
              </td>
              <td>{{ row.origin_city }} -> {{ row.dest_city }}</td>
              <td>{{ row.carrier_name }}</td>
              <td>
                <select class="status-select" :value="row.status" @change="updateStatus(row, $event.target.value)">
                  <option value="pending">pending</option>
                  <option value="in_transit">in transit</option>
                  <option value="delayed">delayed</option>
                  <option value="delivered">delivered</option>
                  <option value="cancelled">cancelled</option>
                </select>
              </td>
              <td><RiskBadge :risk="row.delay_prediction.risk_level" /></td>
              <td><RiskBadge :risk="row.cost_prediction.risk_level" /></td>
              <td>{{ row.scheduled_date }}</td>
              <td>Rs {{ row.estimated_cost.toLocaleString('en-IN') }}</td>
              <td>
                <button class="icon-button" type="button" title="Open prediction details" @click="openDetails(row)">
                  <Sparkles :size="17" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <div v-if="selected" class="modal-backdrop" @click.self="selected = null">
      <section class="modal-panel" role="dialog" aria-modal="true">
        <div class="section-heading">
          <h2>Shipment #{{ selected.shipment_id }}</h2>
          <button class="icon-button" type="button" title="Close" @click="selected = null">
            <X :size="18" />
          </button>
        </div>
        <div class="detail-grid">
          <div>
            <span class="field-label">Product</span>
            <strong>{{ selected.product_name }}</strong>
          </div>
          <div>
            <span class="field-label">Route</span>
            <strong>{{ selected.origin_city }} -> {{ selected.dest_city }}</strong>
          </div>
          <div>
            <span class="field-label">Distance</span>
            <strong>{{ selected.distance_km.toLocaleString('en-IN') }} km</strong>
          </div>
          <div>
            <span class="field-label">Carrier reliability</span>
            <strong>{{ Math.round(selected.carrier_reliability * 100) }}%</strong>
          </div>
        </div>
        <div class="prediction-pair">
          <article>
            <RiskBadge :risk="selected.delay_prediction.risk_level" />
            <h3>Delay Prediction</h3>
            <p>{{ selected.delay_prediction.explanation }}</p>
          </article>
          <article>
            <RiskBadge :risk="selected.cost_prediction.risk_level" />
            <h3>Cost Overrun</h3>
            <p>{{ selected.cost_prediction.explanation }}</p>
          </article>
        </div>
        <div v-if="livePrediction" class="live-result">
          <RiskBadge :risk="livePrediction.risk_level" />
          <strong>{{ livePrediction.model_name }}</strong>
          <p>{{ livePrediction.explanation }}</p>
        </div>
        <div class="button-row">
          <button class="command-button" type="button" @click="runPrediction('delay')">
            <Sparkles :size="16" />
            Run Delay Model
          </button>
          <button class="command-button secondary" type="button" @click="runPrediction('cost')">
            <Sparkles :size="16" />
            Run Cost Model
          </button>
        </div>
      </section>
    </div>
  </div>
</template>
