import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import Dashboard from '../pages/Dashboard.vue'
import OtherPage from '../pages/OtherPage.vue'

const routes = [
  {
    path: '/',
    component: MainLayout,
    children: [
      { path: 'robots', component: Dashboard },
      { path: 'settings', component: OtherPage },
      { path: 'statistics', component: OtherPage }
    ]
  }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
