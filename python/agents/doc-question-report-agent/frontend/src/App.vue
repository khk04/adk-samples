<template>
  <div id="app">
    <el-container>
      <el-header class="app-header">
        <h1>Document Question & Report Agent</h1>
        <p>문서 분석 및 리포트 생성 시스템</p>
      </el-header>
      
      <el-main class="app-main">
        <router-view />
      </el-main>
      
      <el-footer class="app-footer">
        <p>&copy; 2024 Document Question & Report Agent. All rights reserved.</p>
      </el-footer>
    </el-container>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  min-height: 100vh;
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  text-align: center;
  padding: 20px;
}

.app-header h1 {
  margin: 0 0 10px 0;
  font-size: 2.5em;
}

.app-header p {
  margin: 0;
  opacity: 0.9;
}

.app-main {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.app-footer {
  background-color: #f5f5f5;
  text-align: center;
  padding: 20px;
  color: #666;
}
</style>