<script setup lang="ts">

import {onMounted, watch} from "vue";
import {BaseState, useBaseStore} from "@/stores/base.ts";
import {Dict, DictType} from "@/types.ts"
import {useRuntimeStore} from "@/stores/runtime.ts";
import {useSettingStore} from "@/stores/setting.ts";
import {cloneDeep} from "lodash-es";
import Backgorund from "@/components/Backgorund.vue";
import useTheme from "@/hooks/theme.ts";
import * as localforage from "localforage";
import SettingDialog from "@/components/dialog/SettingDialog.vue";
import ArticleContentDialog from "@/components/dialog/ArticleContentDialog.vue";
import CollectNotice from "@/components/CollectNotice.vue";
import {SAVE_SETTING_KEY, SAVE_DICT_KEY} from "@/utils/const.ts";
import {shakeCommonDict} from "@/utils";
import router from "@/router.ts";

const store = useBaseStore()
const runtimeStore = useRuntimeStore()
const settingStore = useSettingStore()
const {setTheme} = useTheme()

watch(store.$state, (n: BaseState) => {
  localforage.setItem(SAVE_DICT_KEY.key, JSON.stringify({val: shakeCommonDict(n), version: SAVE_DICT_KEY.version}))
})

watch(settingStore.$state, (n) => {
  localStorage.setItem(SAVE_SETTING_KEY.key, JSON.stringify({val: n, version: SAVE_SETTING_KEY.version}))
})

//检测几个特定词典
watch(store.collect.originWords, (n) => {
  if (n.length === 0) {
    store.collect.words = []
    store.collect.chapterWords = []
  } else {
    store.collect.words = cloneDeep(n)
    store.collect.chapterWords = [store.collect.words]
  }
})
watch(store.simple.originWords, (n) => {
  if (n.length === 0) {
    store.simple.words = []
    store.simple.chapterWords = []
  } else {
    store.simple.words = cloneDeep(n)
    store.simple.chapterWords = [store.simple.words]
  }
})
watch(store.wrong.originWords, (n) => {
  if (n.length === 0) {
    store.wrong.words = []
    store.wrong.chapterWords = []
  } else {
    store.wrong.words = cloneDeep(n)
    store.wrong.chapterWords = [store.wrong.words]
  }
})

async function init() {
  // console.time()
  store.init().then(() => {
    store.load = true
    // console.timeEnd()
  })
  await settingStore.init()
  setTheme(settingStore.theme)
}

// 检查用户是否已在主项目中登录
async function checkLoginStatus() {
  // 不再跳过登录检查，确保所有环境都验证登录状态
  
  try {
    // 获取主项目的域名和端口
    let mainAppUrl = '';
    
    // 1. 首先检查是否有环境变量（Docker环境）
    if (import.meta.env.VITE_MAIN_APP_URL || import.meta.env.MAIN_APP_URL) {
      mainAppUrl = import.meta.env.VITE_MAIN_APP_URL || import.meta.env.MAIN_APP_URL;
      console.log('使用环境变量中的主项目URL:', mainAppUrl);
    }
    // 2. 如果是生产环境但没有环境变量，则从当前URL推断
    else if (process.env.NODE_ENV === 'production') {
      // 修改：在Docker环境中，如果URL包含3000端口，则替换为5001
      // 如果不包含端口号，则直接使用原始URL
      const currentOrigin = window.location.origin;
      if (currentOrigin.includes(':3000')) {
        mainAppUrl = currentOrigin.replace(':3000', ':5001');
      } else {
        // 如果是在服务器上直接访问3000端口，则使用相同的主机名但端口为5001
        const hostname = window.location.hostname;
        mainAppUrl = `http://${hostname}:5001`;
      }
      console.log('从当前URL推断主项目URL:', mainAppUrl);
    }
    // 3. 开发环境使用空字符串（通过代理访问）
    else {
      console.log('使用开发环境代理访问主项目API');
    }
    
    // 调用主项目的登录状态检查API
    const response = await fetch(`${mainAppUrl}/api/check_login_status`, {
      method: 'GET',
      credentials: 'include', // 包含跨域请求的cookies
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    
    // 如果未登录，重定向到主项目的登录页面
    if (!data.logged_in) {
      console.log('用户未登录，重定向到主项目登录页面')
      
      // 获取主项目URL（用于重定向）
      let loginUrl;
      
      // 1. 首先检查是否有环境变量（Docker环境）
      if (import.meta.env.VITE_MAIN_APP_URL || import.meta.env.MAIN_APP_URL) {
        loginUrl = import.meta.env.VITE_MAIN_APP_URL || import.meta.env.MAIN_APP_URL;
      }
      // 2. 如果是生产环境但没有环境变量，则从当前URL推断
      else if (process.env.NODE_ENV === 'production') {
        // 修改：与上面相同的逻辑处理登录URL
        const currentOrigin = window.location.origin;
        if (currentOrigin.includes(':3000')) {
          loginUrl = currentOrigin.replace(':3000', ':5001');
        } else {
          const hostname = window.location.hostname;
          loginUrl = `http://${hostname}:5001`;
        }
      }
      // 3. 开发环境使用硬编码的URL
      else {
        loginUrl = 'http://localhost:5001';
      }
      
      window.location.href = `${loginUrl}/?redirect=${encodeURIComponent(window.location.href)}`
      return false
    }
    
    console.log('用户已登录:', data.username)
    return true
  } catch (error) {
    console.error('检查登录状态时出错:', error)
    // 在出错时，不再跳过登录检查，而是提示用户登录
    console.log('登录检查出错，提示用户登录');
    
    // 获取主项目URL（用于重定向）
    let loginUrl;
    
    // 1. 首先检查是否有环境变量（Docker环境）
    if (import.meta.env.VITE_MAIN_APP_URL || import.meta.env.MAIN_APP_URL) {
      loginUrl = import.meta.env.VITE_MAIN_APP_URL || import.meta.env.MAIN_APP_URL;
    }
    // 2. 如果是生产环境但没有环境变量，则从当前URL推断
    else if (process.env.NODE_ENV === 'production') {
      // 修改：与上面相同的逻辑处理登录URL
      const currentOrigin = window.location.origin;
      if (currentOrigin.includes(':3000')) {
        loginUrl = currentOrigin.replace(':3000', ':5001');
      } else {
        const hostname = window.location.hostname;
        loginUrl = `http://${hostname}:5001`;
      }
    }
    // 3. 开发环境使用硬编码的URL
    else {
      loginUrl = 'http://localhost:5001';
    }
    
    // 显示登录提示，并提供登录链接
    alert('请先登录主系统后再使用此功能！');
    window.location.href = `${loginUrl}/?redirect=${encodeURIComponent(window.location.href)}`;
    return false;
  }
}

onMounted(async () => {
  // 首先检查登录状态
  const isLoggedIn = await checkLoginStatus()
  
  // 只有在已登录的情况下才初始化应用
  if (isLoggedIn) {
    init()
  }

  if (/Mobi|Android|iPhone/i.test(navigator.userAgent)) {
    // 当前设备是移动设备
    console.log('当前设备是移动设备')
    // router.replace('/mobile')
  }
})
</script>

<template>
  <Backgorund/>
  <router-view/>
  <CollectNotice/>
  <ArticleContentDialog/>
  <SettingDialog/>
</template>

<style scoped lang="scss">
@import "@/assets/css/variable";

.main-page {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  overflow: hidden;
  font-size: 14rem;
  display: flex;
  justify-content: center;
}
</style>
