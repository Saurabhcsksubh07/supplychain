import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import Dashboard from './views/Dashboard.vue'
import Inventory from './views/Inventory.vue'
import Predictions from './views/Predictions.vue'
import Shipments from './views/Shipments.vue'
import './styles.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'dashboard', component: Dashboard },
    { path: '/shipments', name: 'shipments', component: Shipments },
    { path: '/inventory', name: 'inventory', component: Inventory },
    { path: '/predictions', name: 'predictions', component: Predictions },
  ],
})

createApp(App).use(router).mount('#app')
