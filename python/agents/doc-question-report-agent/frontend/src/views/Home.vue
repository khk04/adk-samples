<template>
  <div class="home">
    <el-row :gutter="20" justify="center">
      <el-col :span="20">
        <el-card class="welcome-card">
          <div class="welcome-header">
            <el-icon class="welcome-icon"><Document /></el-icon>
            <h1>Document Question & Report Agent</h1>
            <p class="welcome-subtitle">AI 기반 문서 분석 및 보고서 생성 시스템</p>
          </div>
          
          <div class="workflow-steps">
            <h2>📋 작업 흐름</h2>
            <el-steps :active="currentStep" finish-status="success" align-center>
              <el-step title="문서 업로드" description="분석할 문서를 업로드합니다" />
              <el-step title="질문 생성" description="AI가 문서 내용을 분석하여 질문을 생성합니다" />
              <el-step title="질문 선택" description="원하는 분석 내용을 선택합니다" />
              <el-step title="리포트 생성" description="선택된 내용을 바탕으로 리포트를 생성합니다" />
              <el-step title="다운로드" description="완성된 리포트를 다운로드합니다" />
            </el-steps>
          </div>

          <div class="action-buttons">
            <el-button 
              type="primary" 
              size="large" 
              @click="startWorkflow"
              :disabled="!isApiHealthy"
            >
              <el-icon><Upload /></el-icon>
              문서 업로드 시작
            </el-button>
            
            <el-button 
              type="info" 
              size="large" 
              @click="checkApiHealth"
              :loading="healthChecking"
            >
              <el-icon><Connection /></el-icon>
              API 상태 확인
            </el-button>
          </div>

          <div class="status-info">
            <el-alert
              v-if="!isApiHealthy"
              title="API 서버 연결 필요"
              type="warning"
              description="문서 처리를 위해 백엔드 API 서버가 실행 중이어야 합니다."
              show-icon
              :closable="false"
            />
            
            <el-alert
              v-else
              title="시스템 준비 완료"
              type="success"
              description="모든 서비스가 정상적으로 실행 중입니다. 문서 업로드를 시작할 수 있습니다."
              show-icon
              :closable="false"
            />
          </div>
        </el-card>

        <el-card class="features-card">
          <h3>🚀 주요 기능</h3>
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="feature-item">
                <el-icon class="feature-icon"><Document /></el-icon>
                <h4>다양한 문서 형식 지원</h4>
                <p>PDF, DOCX, TXT, HTML, CSV, Excel 등 다양한 형식의 문서를 처리할 수 있습니다.</p>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="feature-item">
                <el-icon class="feature-icon"><ChatDotRound /></el-icon>
                <h4>AI 기반 질문 생성</h4>
                <p>문서 내용을 분석하여 관련성 높은 질문을 자동으로 생성합니다.</p>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="feature-item">
                <el-icon class="feature-icon"><DataAnalysis /></el-icon>
                <h4>맞춤형 리포트 생성</h4>
                <p>사용자가 선택한 내용을 바탕으로 전문적인 리포트를 생성합니다.</p>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Document, Upload, Connection, ChatDotRound, DataAnalysis } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

export default {
  name: 'Home',
  components: {
    Document,
    Upload,
    Connection,
    ChatDotRound,
    DataAnalysis
  },
  setup() {
    const router = useRouter()
    const currentStep = ref(0)
    const isApiHealthy = ref(false)
    const healthChecking = ref(false)

    const checkApiHealth = async () => {
      healthChecking.value = true
      try {
        const apiUrl = process.env.VUE_APP_API_URL ? `${process.env.VUE_APP_API_URL}/health` : '/api/health'
        const response = await axios.get(apiUrl)
        if (response.data.status === 'healthy') {
          isApiHealthy.value = true
          ElMessage.success('API 서버가 정상적으로 실행 중입니다!')
        }
      } catch (error) {
        isApiHealthy.value = false
        ElMessage.error('API 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.')
      } finally {
        healthChecking.value = false
      }
    }

    const startWorkflow = () => {
      router.push('/upload')
    }

    onMounted(() => {
      checkApiHealth()
    })

    return {
      currentStep,
      isApiHealthy,
      healthChecking,
      checkApiHealth,
      startWorkflow
    }
  }
}
</script>

<style scoped>
.home {
  padding: 20px 0;
}

.welcome-card {
  text-align: center;
  margin-bottom: 30px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.welcome-header {
  margin-bottom: 40px;
}

.welcome-icon {
  font-size: 4rem;
  color: #667eea;
  margin-bottom: 20px;
}

.welcome-header h1 {
  font-size: 2.5rem;
  color: #2c3e50;
  margin: 20px 0 10px 0;
  font-weight: 700;
}

.welcome-subtitle {
  font-size: 1.2rem;
  color: #7f8c8d;
  margin: 0;
}

.workflow-steps {
  margin: 40px 0;
}

.workflow-steps h2 {
  color: #2c3e50;
  margin-bottom: 30px;
  font-weight: 600;
}

.action-buttons {
  margin: 40px 0;
  display: flex;
  gap: 20px;
  justify-content: center;
  flex-wrap: wrap;
}

.status-info {
  margin-top: 30px;
}

.features-card {
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.features-card h3 {
  color: #2c3e50;
  margin-bottom: 30px;
  font-weight: 600;
  text-align: center;
}

.feature-item {
  text-align: center;
  padding: 20px;
}

.feature-icon {
  font-size: 3rem;
  color: #667eea;
  margin-bottom: 20px;
}

.feature-item h4 {
  color: #2c3e50;
  margin: 15px 0 10px 0;
  font-weight: 600;
}

.feature-item p {
  color: #7f8c8d;
  line-height: 1.6;
  margin: 0;
}

/* 반응형 디자인 */
@media (max-width: 768px) {
  .welcome-header h1 {
    font-size: 2rem;
  }
  
  .action-buttons {
    flex-direction: column;
    align-items: center;
  }
  
  .el-col {
    margin-bottom: 20px;
  }
}
</style>