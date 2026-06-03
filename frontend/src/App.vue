<script setup>
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { Boxes, BrainCircuit, LayoutDashboard, PackageCheck, Truck } from 'lucide-vue-next'

const route = useRoute()
const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/shipments', label: 'Shipments', icon: Truck },
  { to: '/inventory', label: 'Inventory', icon: Boxes },
  { to: '/predictions', label: 'Predictions', icon: BrainCircuit },
]
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar" aria-label="Primary navigation">
      <RouterLink to="/" class="brand" aria-label="Supply Chain Command Centre home">
        <span class="brand-mark"><PackageCheck :size="22" /></span>
        <span>
          <strong>Command Centre</strong>
          <small>Predictive Supply Chain</small>
        </span>
      </RouterLink>

      <nav class="nav-list">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="nav-item"
          :class="{ active: route.path === item.to }"
        >
          <component :is="item.icon" :size="18" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
    </aside>

    <main class="main-panel">
      <RouterView />
    </main>
  </div>
</template>
