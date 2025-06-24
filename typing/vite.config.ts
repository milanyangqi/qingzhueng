import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from "@vitejs/plugin-vue-jsx";
import {resolve} from 'path'
import {visualizer} from "rollup-plugin-visualizer";
import {ElementPlusResolver} from "unplugin-vue-components/resolvers";
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import {getLastCommit} from "git-last-commit";

function pathResolve(dir:string) {
  return resolve(__dirname, ".", dir)
}

const lifecycle = process.env.npm_lifecycle_event;


// https://vitejs.dev/config/
export default defineConfig(async () => {
  let latestCommitHash = 'unknown';
  
  // 在Docker环境中跳过Git操作
  if (!process.env.DOCKER_BUILD) {
    try {
      latestCommitHash = await new Promise<string>((resolve, reject) => {
        return getLastCommit((err, commit) => {
          if (err) {
            resolve('unknown');
          } else {
            resolve(commit.shortHash);
          }
        });
      });
    } catch (error) {
      latestCommitHash = 'unknown';
    }
  }
  return {
    plugins: [
      vue({
        reactivityTransform: true
      }),
      AutoImport({
        resolvers: [ElementPlusResolver()],
      }),
      Components({
        resolvers: [ElementPlusResolver()],
      }),
      vueJsx(),
      lifecycle === 'report' ?
        visualizer({
          gzipSize: true,
          brotliSize: true,
          emitFile: false,
          filename: "report.html", //分析图生成的文件名
          open: true //如果存在本地服务端口，将在打包后自动展示
        }) : null,
    ],
    define: {
      LATEST_COMMIT_HASH: JSON.stringify(latestCommitHash + (process.env.NODE_ENV === 'production' ? '' : ' (dev)')),
    },
    //修改为子路径部署，以便在主项目下访问
    base: '/typing/',
    resolve: {
      alias: {
        "@": pathResolve("src"),
      },
      extensions: ['.mjs', '.js', '.ts', '.jsx', '.tsx', '.json', '.vue']
    },
    server: {
      port: 3000,
      open: false,
      host: '0.0.0.0',
      fs: {
        strict: false,
      },
      proxy: {
        '/api': {
          target: process.env.VITE_MAIN_APP_URL || 'http://localhost:5001',
          changeOrigin: true,
          secure: false,
          credentials: 'include',
          // 添加更多配置以解决跨域问题
          rewrite: (path) => path,
          headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,PUT,POST,DELETE,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
          }
        }
      },
      cors: true
    }
  }
})
