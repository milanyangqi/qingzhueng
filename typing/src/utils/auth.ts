import axios from 'axios'

// 配置axios默认设置
axios.defaults.withCredentials = true

// 主项目API基础URL
const MAIN_PROJECT_API = 'http://localhost:5001'

/**
 * 检查用户登录状态
 * @returns Promise<boolean> 是否已登录
 */
export async function checkLoginStatus(): Promise<boolean> {
  try {
    const response = await axios.get(`${MAIN_PROJECT_API}/api/check_login`)
    return response.data.logged_in === true
  } catch (error) {
    console.error('检查登录状态失败:', error)
    return false
  }
}

/**
 * 重定向到主项目登录页面
 */
export function redirectToMainProject(): void {
  window.location.href = MAIN_PROJECT_API
}

/**
 * 认证守卫函数
 * 如果用户未登录，返回false但不自动重定向
 */
export async function authGuard(): Promise<boolean> {
  const isLoggedIn = await checkLoginStatus()
  return isLoggedIn
}

/**
 * 严格认证守卫函数
 * 如果用户未登录，自动重定向到主项目
 */
export async function strictAuthGuard(): Promise<boolean> {
  const isLoggedIn = await checkLoginStatus()
  
  if (!isLoggedIn) {
    redirectToMainProject()
    return false
  }
  
  return true
}

/**
 * 定期检查登录状态
 * @param interval 检查间隔（毫秒），默认5分钟
 */
export function startAuthCheck(interval: number = 5 * 60 * 1000): void {
  setInterval(async () => {
    const isLoggedIn = await checkLoginStatus()
    if (!isLoggedIn) {
      alert('登录已过期，请重新登录')
      redirectToMainProject()
    }
  }, interval)
}