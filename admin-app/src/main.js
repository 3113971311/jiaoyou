import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import {
  DataAnalysis, PictureFilled, Goods, UserFilled,
  ChatDotSquare, WarningFilled, Setting, Search,
  Delete, Edit, Plus, Check, Close, ArrowLeft,
  Refresh, SwitchButton, Warning, List, Grid,
  Upload, Download, Filter, Sort, Lock, User,
  ArrowDown,
} from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import './assets/global.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus)

const icons = {
  DataAnalysis, PictureFilled, Goods, UserFilled,
  ChatDotSquare, WarningFilled, Setting, Search,
  Delete, Edit, Plus, Check, Close, ArrowLeft,
  Refresh, SwitchButton, Warning, List, Grid,
  Upload, Download, Filter, Sort, Lock, User,
  ArrowDown,
}
for (const [k, c] of Object.entries(icons)) app.component(k, c)

app.mount('#app')
