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

// 全局路由守卫
router.beforeEach(async (to, from, next) => {
    const isAuthenticated = await strictAuthGuard()
    if (isAuthenticated) {
        next()
    }
    // 如果未认证，strictAuthGuard会自动重定向，这里不需要调用next()
})

export default router