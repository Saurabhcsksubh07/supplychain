<script setup>
defineProps({
  risk: { type: String, default: 'LOW' },
})
</script>

<template>
  <span class="risk-badge" :class="`risk-${risk.toLowerCase()}`">{{ risk }}</span>
</template>
