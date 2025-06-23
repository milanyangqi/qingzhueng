import {createApp} from 'vue'
import './assets/css/style.scss'
import App from './App.vue'
// import Mobile from './Mobile.vue'
import {createPinia} from "pinia"
// import ElementPlus from 'element-plus'
import ZH from "@/locales/zh-CN.ts";
import {createI18n} from 'vue-i18n'
import router from "@/router.ts";
import VueVirtualScroller from 'vue-virtual-scroller'
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css'
import { strictAuthGuard, startAuthCheck, checkLoginStatus } from '@/utils/auth'

const i18n = createI18n({
  locale: 'zh-CN',
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': ZH
  },
})

const pinia = createPinia()
// const app = createApp(Mobile)
const app = createApp(App)

app.use(VueVirtualScroller)
// app.use(ElementPlus)
app.use(pinia)
app.use(i18n)
app.use(router)

// 在应用启动前检查登录状态
checkLoginStatus().then(isLoggedIn => {
  // 无论是否登录都挂载应用
  app.mount('#app')
  
  if (isLoggedIn) {
    // 启动定期认证检查（每5分钟检查一次）
    startAuthCheck()
  }
})