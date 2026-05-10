import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as Icons from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import './assets/global.css'
const app = createApp(App)
app.use(createPinia()); app.use(router); app.use(ElementPlus)
for (const [k, c] of Object.entries(Icons)) app.component(k, c)
app.mount('#app')
