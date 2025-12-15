// Vue Router configuration with routes for Dashboard, Files, Configs, and Node Editor views.

import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '../views/DashboardView.vue'
import FilesView from '../views/FilesView.vue'
import ConfigsView from '../views/ConfigsView.vue'
import NodeEditorView from '../views/NodeEditorView.vue'

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
    },
    {
      path: '/editor',
      name: 'editor',
      component: NodeEditorView
    }
  ]
})

export default router
