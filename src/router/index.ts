import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import Dashboard from '../pages/Dashboard.vue'
import OtherPage from '../pages/OtherPage.vue'

const routes = [
  {
    path: '/',
    component: MainLayout,
    children: [
      { path: '', component: Dashboard },
      { path: 'other', component: OtherPage }
    ]
  }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
