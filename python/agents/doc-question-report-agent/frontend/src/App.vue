<template>
  <div id="app">
    <el-container>
      <!-- 헤더 -->
      <el-header class="app-header">
        <div class="header-content">
          <h1 class="app-title">
            <el-icon><Document /></el-icon>
            Document Question & Report Agent
          </h1>
          <div class="header-actions">
            <el-button @click="checkHealth" type="primary" size="small">
              <el-icon><Connection /></el-icon>
              API 상태 확인
            </el-button>
          </div>
        </div>
      </el-header>

      <!-- 메인 컨텐츠 -->
      <el-main>
        <router-view />
      </el-main>

      <!-- 푸터 -->
      <el-footer class="app-footer">
        <p>&copy; 2024 Document Question & Report Agent. All rights reserved.</p>
      </el-footer>
    </el-container>
  </div>
</template>

<script>
import { Document, Connection } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

export default {
  name: 'App',
  components: {
    Document,
    Connection
  },
  methods: {
    async checkHealth() {
      try {
        const apiUrl = process.env.VUE_APP_API_URL ? `${process.env.VUE_APP_API_URL}/health` : '/api/health'
        const response = await axios.get(apiUrl)
        if (response.data.status === 'healthy') {
          ElMessage.success('API 서버가 정상적으로 실행 중입니다!')
        }
      } catch (error) {
        ElMessage.error('API 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.')
      }
    }
  }
}
</script>

<style>
#app {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  height: 100vh;
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  padding: 0 20px;
}

.app-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.el-main {
  background-color: #f5f7fa;
  min-height: calc(100vh - 120px);
  padding: 20px;
}

.app-footer {
  background-color: #2c3e50;
  color: white;
  text-align: center;
  padding: 15px;
  font-size: 0.9rem;
}

/* 전역 스타일 */
.el-card {
  margin-bottom: 20px;
}

.el-button {
  border-radius: 8px;
}

.el-input {
  border-radius: 8px;
}

.el-upload {
  border-radius: 8px;
}
</style>