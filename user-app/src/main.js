import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import {
  Search, ChatDotSquare, Star, Money, StarFilled,
  ArrowLeft, Back, PictureFilled, Location, Loading, User,
  Lock, Message, SwitchButton, Plus, Delete, Edit,
  Camera, Close, Check, Clock, Upload, InfoFilled,
  Warning, ArrowRight, Share, MoreFilled, Calendar,
  Grid, List, Sort, Filter, Download, UploadFilled,
  Bell, Position, Folder, FolderOpened, ChatLineSquare,
} from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import './assets/global.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus)

const icons = {
  Search, ChatDotSquare, Star, Money, StarFilled,
  ArrowLeft, Back, PictureFilled, Location, Loading, User,
  Lock, Message, SwitchButton, Plus, Delete, Edit,
  Camera, Close, Check, Clock, Upload, InfoFilled,
  Warning, ArrowRight, Share, MoreFilled, Calendar,
  Grid, List, Sort, Filter, Download, UploadFilled,
  Bell, Position, Folder, FolderOpened, ChatLineSquare,
}
for (const [k, c] of Object.entries(icons)) app.component(k, c)

app.mount('#app')
