<template>
  <div class="report-generation">
    <el-card class="report-card">
      <template #header>
        <div class="card-header">
          <span>리포트 생성</span>
          <el-button @click="$router.push('/')" type="text" size="small">
            <el-icon><Back /></el-icon>
            홈으로 돌아가기
          </el-button>
        </div>
      </template>

      <!-- 리포트 생성 정보 -->
      <div v-if="reportRequest" class="report-info">
        <el-alert
          :title="`문서 ID: ${reportRequest.document_id}`"
          type="info"
          :closable="false"
          show-icon
        />
        
        <div class="selected-questions-summary">
          <h4>선택된 질문들:</h4>
          <el-tag 
            v-for="(question, index) in reportRequest.selected_questions" 
            :key="index"
            class="question-tag"
            type="primary"
          >
            {{ question.text }}
          </el-tag>
        </div>
      </div>

      <!-- 리포트 생성 옵션 -->
      <div class="report-options">
        <h3>리포트 생성 옵션</h3>
        
        <el-form :model="reportOptions" label-width="120px" class="options-form">
          <el-form-item label="리포트 유형">
            <el-select v-model="reportOptions.report_type" placeholder="리포트 유형을 선택하세요">
              <el-option label="분석 리포트" value="analysis" />
              <el-option label="요약 리포트" value="summary" />
              <el-option label="상세 리포트" value="detailed" />
              <el-option label="비교 분석" value="comparison" />
            </el-select>
          </el-form-item>

          <el-form-item label="리포트 언어">
            <el-radio-group v-model="reportOptions.language">
              <el-radio label="ko">한국어</el-radio>
              <el-radio label="en">영어</el-radio>
              <el-radio label="ja">일본어</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="리포트 길이">
            <el-radio-group v-model="reportOptions.length">
              <el-radio label="short">간단 (1-2페이지)</el-radio>
              <el-radio label="medium">보통 (3-5페이지)</el-radio>
              <el-radio label="long">상세 (6페이지 이상)</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="추가 요구사항">
            <el-input
              v-model="reportOptions.additional_requirements"
              type="textarea"
              :rows="3"
              placeholder="리포트에 포함하고 싶은 추가 요구사항이나 특별한 형식이 있다면 입력해주세요."
            />
          </el-form-item>
        </el-form>
      </div>

      <!-- 리포트 생성 버튼 -->
      <div class="generate-actions">
        <el-button 
          type="primary" 
          size="large" 
          @click="generateReport"
          :loading="generating"
          :disabled="!canGenerateReport"
        >
          <el-icon><DocumentCopy /></el-icon>
          {{ generating ? '리포트 생성 중...' : '리포트 생성하기' }}
        </el-button>
      </div>

      <!-- 생성된 리포트 -->
      <div v-if="generatedReport" class="generated-report">
        <h3>생성된 리포트</h3>
        
        <!-- 리포트 메타데이터 -->
        <div class="report-metadata">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="리포트 ID">{{ generatedReport.report_id }}</el-descriptions-item>
            <el-descriptions-item label="생성 시간">{{ formatTime(generatedReport.created_at) }}</el-descriptions-item>
            <el-descriptions-item label="리포트 유형">{{ generatedReport.report_type }}</el-descriptions-item>
            <el-descriptions-item label="상태">{{ generatedReport.status }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 리포트 내용 -->
        <div class="report-content">
          <h4>리포트 내용</h4>
          <div class="content-preview">
            <div v-html="generatedReport.content" class="report-text"></div>
          </div>
        </div>

        <!-- 리포트 액션 -->
        <div class="report-actions">
          <el-button type="success" @click="downloadReport">
            <el-icon><Download /></el-icon>
            리포트 다운로드
          </el-button>
          <el-button type="warning" @click="editReport">
            <el-icon><Edit /></el-icon>
            리포트 수정
          </el-button>
          <el-button type="info" @click="shareReport">
            <el-icon><Share /></el-icon>
            공유하기
          </el-button>
        </div>

        <!-- 피드백 및 재생성 -->
        <div class="feedback-section">
          <h4>피드백 및 개선</h4>
          <el-input
            v-model="feedbackText"
            type="textarea"
            :rows="3"
            placeholder="리포트에 대한 피드백을 입력해주세요. 개선사항이 있다면 자세히 설명해주세요."
          />
          <div class="feedback-actions">
            <el-button type="primary" @click="submitFeedback" :disabled="!feedbackText.trim()">
              피드백 제출
            </el-button>
            <el-button type="warning" @click="regenerateReport" :disabled="!feedbackText.trim()">
              피드백 반영하여 재생성
            </el-button>
          </div>
        </div>
      </div>

      <!-- 로딩 상태 -->
      <div v-if="generating" class="generation-status">
        <el-card class="status-card">
          <div class="status-content">
            <el-icon class="loading-icon" size="60" color="#409EFF">
              <Loading />
            </el-icon>
            <h3>리포트를 생성중입니다...</h3>
            <p>AI가 선택된 질문들을 분석하여 전문적인 리포트를 작성하고 있습니다.</p>
            <el-progress :percentage="generationProgress" :status="generationStatus" />
          </div>
        </el-card>
      </div>
    </el-card>
  </div>
</template>

<script>
import { 
  Back, 
  DocumentCopy, 
  Download, 
  Edit, 
  Share, 
  Loading 
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

export default {
  name: 'ReportGeneration',
  components: {
    Back,
    DocumentCopy,
    Download,
    Edit,
    Share,
    Loading
  },
  data() {
    return {
      reportRequest: null,
      reportOptions: {
        report_type: 'analysis',
        language: 'ko',
        length: 'medium',
        additional_requirements: ''
      },
      generating: false,
      generatedReport: null,
      generationProgress: 0,
      generationStatus: '',
      feedbackText: ''
    }
  },
  computed: {
    canGenerateReport() {
      return this.reportRequest && this.reportRequest.selected_questions.length > 0
    }
  },
  mounted() {
    this.loadReportRequest()
  },
  methods: {
    loadReportRequest() {
      // URL 쿼리에서 리포트 요청 정보 로드
      const documentId = this.$route.query.document_id
      const questions = this.$route.query.questions

      if (documentId && questions) {
        try {
          this.reportRequest = {
            document_id: documentId,
            selected_questions: JSON.parse(questions)
          }
        } catch (error) {
          console.error('리포트 요청 정보 파싱 실패:', error)
          ElMessage.error('리포트 요청 정보를 불러올 수 없습니다.')
        }
      } else {
        ElMessage.warning('문서와 질문 정보가 필요합니다.')
        this.$router.push('/questions')
      }
    },

    async generateReport() {
      if (!this.canGenerateReport) {
        ElMessage.warning('리포트를 생성할 수 있는 정보가 부족합니다.')
        return
      }

      this.generating = true
      this.generationProgress = 0
      this.generationStatus = ''

      try {
        // 리포트 생성 요청
        const requestData = {
          document_id: this.reportRequest.document_id,
          selected_questions: this.reportRequest.selected_questions,
          options: this.reportOptions
        }

        // 진행률 시뮬레이션
        const progressInterval = setInterval(() => {
          if (this.generationProgress < 90) {
            this.generationProgress += Math.random() * 10
          }
        }, 500)

        const apiUrl = process.env.VUE_APP_API_URL ? `${process.env.VUE_APP_API_URL}/report` : '/api/report'
        const response = await axios.post(apiUrl, requestData)

        clearInterval(progressInterval)
        this.generationProgress = 100
        this.generationStatus = 'success'

        if (response.data) {
          this.generatedReport = response.data
          ElMessage.success('리포트가 성공적으로 생성되었습니다!')
        }
      } catch (error) {
        console.error('리포트 생성 실패:', error)
        this.generationStatus = 'exception'
        ElMessage.error('리포트 생성에 실패했습니다. 다시 시도해주세요.')
      } finally {
        this.generating = false
        this.generationProgress = 0
      }
    },

    async submitFeedback() {
      if (!this.feedbackText.trim()) {
        ElMessage.warning('피드백을 입력해주세요.')
        return
      }

      try {
        // 피드백 제출 API 호출
        const feedbackUrl = process.env.VUE_APP_API_URL ? `${process.env.VUE_APP_API_URL}/report/${this.generatedReport.report_id}/feedback` : `/api/report/${this.generatedReport.report_id}/feedback`
        await axios.post(feedbackUrl, {
          feedback: this.feedbackText
        })

        ElMessage.success('피드백이 성공적으로 제출되었습니다!')
        this.feedbackText = ''
      } catch (error) {
        console.error('피드백 제출 실패:', error)
        ElMessage.error('피드백 제출에 실패했습니다.')
      }
    },

    async regenerateReport() {
      if (!this.feedbackText.trim()) {
        ElMessage.warning('피드백을 입력해주세요.')
        return
      }

      try {
        // 리포트 재생성 API 호출
        const regenerateUrl = process.env.VUE_APP_API_URL ? `${process.env.VUE_APP_API_URL}/report/${this.generatedReport.report_id}/regenerate` : `/api/report/${this.generatedReport.report_id}/regenerate`
        const response = await axios.post(regenerateUrl, {
          feedback: this.feedbackText
        })

        if (response.data) {
          this.generatedReport = response.data
          ElMessage.success('피드백을 반영한 새로운 리포트가 생성되었습니다!')
          this.feedbackText = ''
        }
      } catch (error) {
        console.error('리포트 재생성 실패:', error)
        ElMessage.error('리포트 재생성에 실패했습니다.')
      }
    },

    downloadReport() {
      // 리포트 다운로드 로직
      ElMessage.info('리포트 다운로드 기능은 준비 중입니다.')
    },

    editReport() {
      // 리포트 수정 로직
      ElMessage.info('리포트 수정 기능은 준비 중입니다.')
    },

    shareReport() {
      // 리포트 공유 로직
      ElMessage.info('리포트 공유 기능은 준비 중입니다.')
    },

    formatTime(timestamp) {
      if (!timestamp) return '알 수 없음'
      try {
        return new Date(timestamp).toLocaleString('ko-KR')
      } catch {
        return '알 수 없음'
      }
    }
  }
}
</script>

<style scoped>
.report-generation {
  max-width: 1000px;
  margin: 0 auto;
}

.report-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.report-info {
  margin-bottom: 30px;
}

.selected-questions-summary {
  margin-top: 20px;
}

.selected-questions-summary h4 {
  margin-bottom: 15px;
  color: #2c3e50;
}

.question-tag {
  margin-right: 10px;
  margin-bottom: 10px;
}

.report-options {
  margin-bottom: 30px;
}

.report-options h3 {
  margin-bottom: 20px;
  color: #2c3e50;
  border-bottom: 2px solid #409EFF;
  padding-bottom: 10px;
}

.options-form {
  max-width: 600px;
}

.generate-actions {
  text-align: center;
  margin-bottom: 30px;
}

.generated-report {
  margin-top: 30px;
}

.generated-report h3 {
  margin-bottom: 20px;
  color: #2c3e50;
  border-bottom: 2px solid #409EFF;
  padding-bottom: 10px;
}

.report-metadata {
  margin-bottom: 20px;
}

.report-content {
  margin-bottom: 30px;
}

.report-content h4 {
  margin-bottom: 15px;
  color: #2c3e50;
}

.content-preview {
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 20px;
  max-height: 400px;
  overflow-y: auto;
}

.report-text {
  line-height: 1.6;
  color: #2c3e50;
}

.report-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-bottom: 30px;
}

.feedback-section {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #e9ecef;
}

.feedback-section h4 {
  margin-bottom: 15px;
  color: #2c3e50;
}

.feedback-actions {
  margin-top: 15px;
  display: flex;
  gap: 15px;
  justify-content: center;
}

.generation-status {
  margin-top: 30px;
}

.status-card {
  text-align: center;
}

.status-content {
  padding: 40px 20px;
}

.loading-icon {
  margin-bottom: 20px;
  animation: rotate 2s linear infinite;
}

.status-content h3 {
  margin-bottom: 15px;
  color: #2c3e50;
}

.status-content p {
  margin-bottom: 20px;
  color: #606266;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .report-actions {
    flex-direction: column;
  }
  
  .report-actions .el-button {
    width: 100%;
  }
  
  .feedback-actions {
    flex-direction: column;
  }
  
  .feedback-actions .el-button {
    width: 100%;
  }
}
</style>