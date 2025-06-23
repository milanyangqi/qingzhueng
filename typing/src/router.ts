import {createRouter, createWebHashHistory} from 'vue-router'
import Practice from "@/pages/practice/index.vue";
import Dict from '@/pages/dict/index.vue'
import Mobile from '@/pages/mobile/index.vue'
import Test from "@/pages/test.vue";
import { strictAuthGuard } from '@/utils/auth'

const routes: any[] = [
    {path: '/practice', component: Practice},
    {path: '/dict', component: Dict},
    {path: '/mobile', component: Mobile},
    {path: '/test', component: Test},
    {path: '/', redirect: '/practice'},
]

const router = createRouter({
    history: createWebHashHistory(),
    routes,
})

// 不再需要全局路由守卫，因为我们在App.vue中处理登录状态检查和显示
// 登录状态检查现在由App.vue组件负责

export default router