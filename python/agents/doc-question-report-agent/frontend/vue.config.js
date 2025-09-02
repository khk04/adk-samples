const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  
  // 개발 서버 설정
  devServer: {
    port: 3000,
    open: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        pathRewrite: {
          '^/api': ''
        }
      }
    }
  },
  
  // 빌드 설정
  outputDir: 'dist',
  assetsDir: 'static',
  
  // PWA 설정
  pwa: {
    name: 'Document Question & Report Agent',
    short_name: 'DocAgent',
    description: 'AI 기반 문서 분석 및 리포트 생성 시스템',
    theme_color: '#667eea',
    background_color: '#ffffff',
    display: 'standalone',
    orientation: 'portrait',
    scope: '/',
    start_url: '/',
    icons: [
      {
        src: 'favicon-16x16.png',
        sizes: '16x16',
        type: 'image/png'
      },
      {
        src: 'favicon-32x32.png',
        sizes: '32x32',
        type: 'image/png'
      },
      {
        src: 'apple-touch-icon.png',
        sizes: '180x180',
        type: 'image/png'
      }
    ]
  },
  
  // CSS 설정
  css: {
    loaderOptions: {
      scss: {
        additionalData: `@import "@/styles/variables.scss";`
      }
    }
  }
})