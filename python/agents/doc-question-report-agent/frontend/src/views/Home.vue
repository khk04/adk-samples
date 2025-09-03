<template>
  <div class="home">
    <!-- 환영 메시지 -->
    <el-card class="welcome-card">
      <div class="welcome-content">
        <el-icon class="welcome-icon" size="80" color="#409EFF">
          <Document />
        </el-icon>
        <h1>Document Question & Report Agent</h1>
        <p class="welcome-description">
          AI 기반 문서 분석 및 질문 응답, 리포트 생성 시스템에 오신 것을 환영합니다.
        </p>
      </div>
    </el-card>

    <!-- 워크플로우 카드들 -->
    <div class="workflow-cards">
      <!-- 1단계: 문서 업로드 -->
      <el-card class="workflow-card" @click="goToUpload">
        <div class="card-content">
          <el-icon class="card-icon" size="50" color="#67C23A">
            <Upload />
          </el-icon>
          <h3>1단계: 문서 업로드</h3>
          <p>PDF, DOCX, Excel, CSV 등 다양한 형식의 문서를 업로드하세요.</p>
          <el-button type="primary" class="card-button">
            문서 업로드 시작
          </el-button>
        </div>
      </el-card>

      <!-- 2단계: 질문 생성 -->
      <el-card class="workflow-card" @click="goToQuestions">
        <div class="card-content">
          <el-icon class="card-icon" size="50" color="#E6A23C">
            <QuestionFilled />
          </el-icon>
          <h3>2단계: 질문 생성</h3>
          <p>AI가 문서를 분석하여 관련 질문들을 자동으로 생성합니다.</p>
          <el-button type="warning" class="card-button">
            질문 생성하기
          </el-button>
        </div>
      </el-card>

      <!-- 3단계: 리포트 생성 -->
      <el-card class="workflow-card" @click="goToReport">
        <div class="card-content">
          <el-icon class="card-icon" size="50" color="#F56C6C">
            <DocumentCopy />
          </el-icon>
          <h3>3단계: 리포트 생성</h3>
          <p>선택한 질문들을 바탕으로 전문적인 리포트를 생성합니다.</p>
          <el-button type="danger" class="card-button">
            리포트 생성하기
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 시스템 상태 -->
    <el-card class="status-card">
      <template #header>
        <div class="card-header">
          <span>시스템 상태</span>
          <el-button @click="refreshStatus" type="text" size="small">
            <el-icon><Refresh /></el-icon>
            새로고침
          </el-button>
        </div>
      </template>
      <div class="status-content">
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="status-item">
              <el-icon class="status-icon" size="30" color="#67C23A">
                <Connection />
              </el-icon>
              <div class="status-text">
                <h4>API 서버</h4>
                <p :class="apiStatus.class">{{ apiStatus.text }}</p>
              </div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="status-item">
              <el-icon class="status-icon" size="30" color="#409EFF">
                <Document />
              </el-icon>
              <div class="status-text">
                <h4>문서 처리</h4>
                <p>{{ systemStatus.cached_documents || 0 }}개 문서</p>
              </div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="status-item">
              <el-icon class="status-icon" size="30" color="#E6A23C">
                <Clock />
              </el-icon>
              <div class="status-text">
                <h4>시스템 업타임</h4>
                <p>{{ formatUptime(systemStatus.uptime) }}</p>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script>
import { 
  Document, 
  Upload, 
  QuestionFilled, 
  DocumentCopy, 
  Connection, 
  Refresh, 
  Clock 
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

export default {
  name: 'Home',
  components: {
    Document,
    Upload,
    QuestionFilled,
    DocumentCopy,
    Connection,
    Refresh,
    Clock
  },
  data() {
    return {
      apiStatus: {
        text: '확인 중...',
        class: 'status-checking'
      },
      systemStatus: {
        cached_documents: 0,
        uptime: null
      }
    }
  },
  mounted() {
    this.checkApiStatus()
    this.getSystemStatus()
  },
  methods: {
    goToUpload() {
      this.$router.push('/upload')
    },
    goToQuestions() {
      this.$router.push('/questions')
    },
    goToReport() {
      this.$router.push('/report')
    },
    async checkApiStatus() {
      try {
        const apiUrl = process.env.VUE_APP_API_URL ? `${process.env.VUE_APP_API_URL}/health` : '/api/health'
        const response = await axios.get(apiUrl)
        if (response.data.status === 'healthy') {
          this.apiStatus = {
            text: '정상',
            class: 'status-healthy'
          }
        }
      } catch (error) {
        this.apiStatus = {
          text: '연결 실패',
          class: 'status-error'
        }
      }
    },
    async getSystemStatus() {
      try {
        const apiUrl = process.env.VUE_APP_API_URL ? `${process.env.VUE_APP_API_URL}/status` : '/api/status'
        const response = await axios.get(apiUrl)
        this.systemStatus = response.data
      } catch (error) {
        console.error('시스템 상태 조회 실패:', error)
      }
    },
    async refreshStatus() {
      await this.checkApiStatus()
      await this.getSystemStatus()
      ElMessage.success('상태가 새로고침되었습니다.')
    },
    formatUptime(uptime) {
      if (!uptime) return '알 수 없음'
      try {
        const date = new Date(uptime)
        return date.toLocaleString('ko-KR')
      } catch {
        return '알 수 없음'
      }
    }
  }
}
</script>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
}

.welcome-card {
  text-align: center;
  margin-bottom: 30px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.welcome-content {
  padding: 40px 20px;
}

.welcome-icon {
  margin-bottom: 20px;
}

.welcome-content h1 {
  margin: 0 0 15px 0;
  font-size: 2.5rem;
  font-weight: 600;
}

.welcome-description {
  font-size: 1.2rem;
  opacity: 0.9;
  margin: 0;
}

.workflow-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.workflow-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.workflow-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
  border-color: #409EFF;
}

.card-content {
  text-align: center;
  padding: 20px;
}

.card-icon {
  margin-bottom: 15px;
}

.card-content h3 {
  margin: 0 0 15px 0;
  color: #2c3e50;
}

.card-content p {
  margin: 0 0 20px 0;
  color: #606266;
  line-height: 1.6;
}

.card-button {
  width: 100%;
}

.status-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-content {
  padding: 20px 0;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  border-radius: 8px;
  background-color: #f8f9fa;
}

.status-icon {
  flex-shrink: 0;
}

.status-text h4 {
  margin: 0 0 5px 0;
  color: #2c3e50;
  font-size: 1rem;
}

.status-text p {
  margin: 0;
  color: #606266;
  font-size: 0.9rem;
}

.status-healthy {
  color: #67C23A !important;
  font-weight: 600;
}

.status-error {
  color: #F56C6C !important;
  font-weight: 600;
}

.status-checking {
  color: #E6A23C !important;
  font-weight: 600;
}

@media (max-width: 768px) {
  .workflow-cards {
    grid-template-columns: 1fr;
  }
  
  .welcome-content h1 {
    font-size: 2rem;
  }
  
  .status-item {
    flex-direction: column;
    text-align: center;
  }
}
</style>