// Vue Router configuration with routes for Dashboard, Files, and Configs views.

import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '../views/DashboardView.vue'
import FilesView from '../views/FilesView.vue'
import ConfigsView from '../views/ConfigsView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: DashboardView
    },
    {
      path: '/files',
      name: 'files',
      component: FilesView
    },
    {
      path: '/configs',
      name: 'configs',
      component: ConfigsView
    }
  ]
})

export default router
