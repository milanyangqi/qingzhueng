<template>
  <div class="login-required">
    <div class="login-card">
      <div class="icon">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 2C13.1 2 14 2.9 14 4C14 5.1 13.1 6 12 6C10.9 6 10 5.1 10 4C10 2.9 10.9 2 12 2ZM21 9V7L15 1H5C3.89 1 3 1.89 3 3V21C3 22.1 3.89 23 5 23H11V21H5V3H13V9H21Z" fill="currentColor"/>
          <path d="M16 10V12H22V10H16ZM16 14V16H22V14H16ZM16 18V20H22V18H16Z" fill="currentColor"/>
        </svg>
      </div>
      <h2>需要登录</h2>
      <p>请先登录主项目后再访问打字练习系统</p>
      <button @click="redirectToLogin" class="login-btn">
        前往登录
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { redirectToMainProject } from '@/utils/auth'

function redirectToLogin() {
  redirectToMainProject()
}
</script>

<style scoped lang="scss">
.login-required {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.login-card {
  background: white;
  border-radius: 16px;
  padding: 48px 32px;
  text-align: center;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  max-width: 400px;
  width: 90%;
}

.icon {
  color: #667eea;
  margin-bottom: 24px;
  display: flex;
  justify-content: center;
}

h2 {
  color: #2d3748;
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 16px;
}

p {
  color: #718096;
  font-size: 16px;
  line-height: 1.5;
  margin-bottom: 32px;
}

.login-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 12px 32px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
  }
  
  &:active {
    transform: translateY(0);
  }
}
</style>