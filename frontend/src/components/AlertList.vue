<script setup>
import { CheckCircle2 } from 'lucide-vue-next'
import RiskBadge from './RiskBadge.vue'

defineProps({
  alerts: { type: Array, default: () => [] },
})

defineEmits(['resolve'])
</script>

<template>
  <section class="panel alert-panel">
    <div class="section-heading">
      <h2>Active Alerts</h2>
    </div>
    <div v-if="!alerts.length" class="empty-state">No unresolved alerts.</div>
    <ul v-else class="alert-list">
      <li v-for="alert in alerts" :key="alert.alert_id">
        <div>
          <RiskBadge :risk="alert.severity" />
          <strong>{{ alert.title }}</strong>
          <p>{{ alert.message }}</p>
        </div>
        <button class="icon-button" type="button" title="Resolve alert" @click="$emit('resolve', alert.alert_id)">
          <CheckCircle2 :size="18" />
        </button>
      </li>
    </ul>
  </section>
</template>
