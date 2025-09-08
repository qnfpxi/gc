import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0', // 允许所有网络接口访问
    port: 3000, // 更改端口为3000
    strictPort: true,
    allowedHosts: ['cold-snails-return.loca.lt', 'localhost', '127.0.0.1'], // 允许localtunnel域名和本地访问
    cors: true, // 启用CORS
    hmr: {
      overlay: true // 启用错误覆盖
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
  base: '/', // 确保资源路径正确
})