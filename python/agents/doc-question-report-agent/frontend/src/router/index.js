import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import DocumentUpload from '../views/DocumentUpload.vue'
import QuestionGeneration from '../views/QuestionGeneration.vue'
import ReportGeneration from '../views/ReportGeneration.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/upload',
    name: 'DocumentUpload',
    component: DocumentUpload
  },
  {
    path: '/questions',
    name: 'QuestionGeneration',
    component: QuestionGeneration
  },
  {
    path: '/report',
    name: 'ReportGeneration',
    component: ReportGeneration
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router