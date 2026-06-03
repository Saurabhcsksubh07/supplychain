<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  detail: { type: String, default: '' },
  tone: { type: String, default: 'blue' },
  icon: { type: Object, default: null },
})
</script>

<template>
  <article class="kpi-card" :class="`tone-${tone}`">
    <div class="kpi-icon" v-if="icon">
      <component :is="icon" :size="20" />
    </div>
    <div>
      <p>{{ label }}</p>
      <strong>{{ value }}</strong>
      <small v-if="detail">{{ detail }}</small>
    </div>
  </article>
</template>
