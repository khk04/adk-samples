<template>
  <div class="question-generation">
    <el-row :gutter="20" justify="center">
      <el-col :span="20">
        <!-- 진행 단계 표시 -->
        <el-card class="progress-card">
          <el-steps :active="2" finish-status="success" align-center>
            <el-step title="문서 업로드" description="분석할 문서를 업로드합니다" />
            <el-step title="질문 생성" description="AI가 문서 내용을 분석하여 질문을 생성합니다" />
            <el-step title="질문 선택" description="원하는 분석 내용을 선택합니다" />
            <el-step title="리포트 생성" description="선택된 내용을 바탕으로 리포트를 생성합니다" />
            <el-step title="다운로드" description="완성된 리포트를 다운로드합니다" />
          </el-steps>
        </el-card>

        <!-- 문서 정보 표시 -->
        <el-card class="document-info-card">
          <template #header>
            <div class="card-header">
              <el-icon><Document /></el-icon>
              <span>문서 정보</span>
            </div>
          </template>
          
          <div class="document-details">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="문서 ID">{{ documentId }}</el-descriptions-item>
              <el-descriptions-item label="파일명">{{ filename }}</el-descriptions-item>
              <el-descriptions-item label="분석 상태">
                <el-tag type="success">완료</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="처리 시간">{{ formatDate(new Date()) }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>

        <!-- 자동 Step 진행 시스템 -->
        <el-card class="auto-step-card">
          <template #header>
            <div class="card-header">
              <el-icon><DataAnalysis /></el-icon>
              <span>자동 Step 진행 시스템</span>
            </div>
          </template>
          
          <div class="auto-step-info">
            <el-alert
              title="자동 Step 진행 안내"
              type="success"
              description="에이전트가 문서를 분석하여 자동으로 Step별 질문을 생성합니다. 각 단계에서 원하는 질문을 선택하면 다음 단계로 자동 진행됩니다."
              show-icon
              :closable="false"
              class="step-info"
            />
            
            <div class="current-step-display">
              <h4>현재 진행 중: Step {{ currentStep }}</h4>
              <p>{{ getStepDescription(currentStep) }} - {{ getStepDetailDescription(currentStep) }}</p>
              <el-progress 
                :percentage="(currentStep / 5) * 100" 
                :format="(percentage) => `진행률: ${percentage.toFixed(0)}%`"
                :stroke-width="20"
                class="step-progress"
              />
            </div>
          </div>
        </el-card>

        <!-- 질문 생성 진행 상황 -->
        <el-card v-if="generatingQuestions" class="generation-card">
          <template #header>
            <div class="card-header">
              <el-icon><Loading /></el-icon>
              <span>Step {{ currentStep }} 질문 생성 중...</span>
            </div>
          </template>
          
          <div class="generation-progress">
            <el-progress 
              :percentage="generationProgress" 
              :status="generationProgress === 100 ? 'success' : ''"
              :stroke-width="20"
            />
            <p class="progress-text">{{ generationText }}</p>
            
            <div class="generation-steps">
              <el-steps :active="currentGenerationStep" direction="vertical" size="small">
                <el-step title="문서 내용 분석" description="문서의 구조와 내용을 파악합니다" />
                <el-step title="주요 토픽 추출" description="핵심 주제와 키워드를 식별합니다" />
                <el-step title="Step별 질문 생성" description="AI가 Step에 맞는 질문을 생성합니다" />
                <el-step title="질문 우선순위 설정" description="중요도에 따라 질문을 정렬합니다" />
              </el-steps>
            </div>
          </div>
        </el-card>

        <!-- 에이전트 처리 과정 정보 -->
        <el-card v-if="questionSet && !generatingQuestions" class="agent-process-card">
          <template #header>
            <div class="card-header">
              <el-icon><DataAnalysis /></el-icon>
              <span>에이전트 처리 과정</span>
            </div>
          </template>
          
          <div class="agent-process-info">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="처리 단계">Step {{ currentStep }}</el-descriptions-item>
              <el-descriptions-item label="질문 세트 ID">{{ questionSet.question_set_id }}</el-descriptions-item>
              <el-descriptions-item label="문서 ID">{{ questionSet.document_id }}</el-descriptions-item>
              <el-descriptions-item label="생성 시간">{{ formatDateTime(questionSet.generated_at) }}</el-descriptions-item>
              <el-descriptions-item label="질문 수">{{ questionSet.questions.length }}개</el-descriptions-item>
              <el-descriptions-item label="버전">{{ questionSet.version }}</el-descriptions-item>
            </el-descriptions>
            
            <div class="agent-log-section">
              <h4>🤖 AI 에이전트 처리 로그</h4>
              <div class="log-content">
                <p><strong>Step {{ currentStep }} 처리 완료:</strong> AI 에이전트가 문서를 분석하여 {{ questionSet.questions.length }}개의 질문을 생성했습니다.</p>
                <p><strong>처리 시간:</strong> {{ formatDateTime(questionSet.generated_at) }}</p>
                <p><strong>질문 유형:</strong> {{ getQuestionCategories(questionSet.questions) }}</p>
                <p><strong>평균 신뢰도:</strong> {{ getAverageConfidence(questionSet.questions) }}%</p>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 생성된 질문 목록 -->
        <el-card v-if="questionSet && !generatingQuestions" class="questions-card">
          <template #header>
            <div class="card-header">
              <el-icon><ChatDotRound /></el-icon>
              <span>Step {{ currentStep }} 질문 목록</span>
              <el-tag type="info" class="question-count">{{ questionSet.questions.length }}개 질문</el-tag>
              <el-tag type="success" class="step-tag">버전 {{ questionSet.version }}</el-tag>
            </div>
          </template>
          
          <div class="questions-container">
            <div class="questions-header">
              <h3>📋 분석 가능한 질문들</h3>
              <p>리포트에 포함하고 싶은 질문들을 체크박스로 선택해주세요.</p>
            </div>
            
            <div class="questions-list">
              <el-checkbox-group v-model="selectedQuestions" class="question-checkboxes">
                <div 
                  v-for="question in questionSet.questions" 
                  :key="question.question_id"
                  class="question-item"
                >
                  <el-checkbox 
                    :label="question.question_id"
                    class="question-checkbox"
                  >
                    <div class="question-content">
                      <div class="question-text">{{ question.question }}</div>
                      <div class="question-meta">
                        <el-tag size="small" type="primary">{{ question.category }}</el-tag>
                        <el-tag size="small" type="warning">우선순위: {{ question.priority }}</el-tag>
                        <el-tag size="small" type="info">{{ question.suggested_report_type }}</el-tag>
                      </div>
                      <div class="question-context">{{ question.context }}</div>
                    </div>
                  </el-checkbox>
                </div>
              </el-checkbox-group>
            </div>
            
            <div class="selection-summary">
              <el-alert
                v-if="selectedQuestions.length === 0"
                title="질문을 선택해주세요"
                type="info"
                description="리포트 생성을 위해 최소 1개 이상의 질문을 선택해주세요."
                show-icon
                :closable="false"
              />
              
              <el-alert
                v-else
                :title="`${selectedQuestions.length}개 질문 선택됨`"
                type="success"
                :description="`선택된 질문들을 바탕으로 리포트를 생성할 수 있습니다.`"
                show-icon
                :closable="false"
              />
            </div>
          </div>
        </el-card>

        <!-- 리포트 유형 선택 -->
        <el-card v-if="questionSet && !generatingQuestions" class="report-type-card">
          <template #header>
            <div class="card-header">
              <el-icon><DataAnalysis /></el-icon>
              <span>리포트 유형 설정</span>
            </div>
          </template>
          
          <div class="report-type-selection">
            <el-form :model="reportForm" label-width="120px">
              <el-form-item label="리포트 유형">
                <el-select v-model="reportForm.reportType" placeholder="리포트 유형을 선택하세요">
                  <el-option label="집행 요약" value="executive_summary" />
                  <el-option label="기술 분석" value="technical_analysis" />
                  <el-option label="시장 조사" value="market_research" />
                  <el-option label="재무 보고서" value="financial_report" />
                  <el-option label="비교 분석" value="comparative_analysis" />
                  <el-option label="권장사항" value="recommendation" />
                  <el-option label="맞춤형" value="custom" />
                </el-select>
              </el-form-item>
              
              <el-form-item label="추가 요구사항">
                <el-input
                  v-model="reportForm.customRequirements"
                  type="textarea"
                  :rows="3"
                  placeholder="리포트에 포함하고 싶은 추가 요구사항이 있다면 입력해주세요."
                />
              </el-form-item>
              
              <el-form-item label="출력 옵션">
                <el-checkbox-group v-model="reportForm.outputOptions">
                  <el-checkbox label="charts">차트 및 그래프 포함</el-checkbox>
                  <el-checkbox label="summary">집행 요약 포함</el-checkbox>
                  <el-checkbox label="appendices">부록 포함</el-checkbox>
                </el-checkbox-group>
              </el-form-item>
            </el-form>
          </div>
        </el-card>

        <!-- 액션 버튼 -->
        <div class="action-buttons">
          <el-button 
            v-if="!questionSet"
            type="primary" 
            size="large" 
            @click="generateQuestions"
            :loading="generatingQuestions"
          >
            <el-icon><MagicStick /></el-icon>
            AI 에이전트 질문 생성 시작
          </el-button>
          
          <el-button 
            v-if="questionSet && selectedQuestions.length > 0 && currentStep < 5"
            type="warning" 
            size="large" 
            @click="proceedToNextStep"
            :disabled="selectedQuestions.length === 0"
          >
            <el-icon><ArrowRight /></el-icon>
            다음 Step으로 진행 ({{ currentStep + 1 }}/5)
          </el-button>
          
          <el-button 
            v-if="questionSet && selectedQuestions.length > 0 && currentStep >= 5"
            type="success" 
            size="large" 
            @click="proceedToReport"
            :disabled="selectedQuestions.length === 0"
          >
            <el-icon><ArrowRight /></el-icon>
            최종 단계: 리포트 생성
          </el-button>
          
          <el-button 
            size="large" 
            @click="goBack"
          >
            <el-icon><ArrowLeft /></el-icon>
            이전 단계로
          </el-button>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { 
  Document, Loading, ChatDotRound, DataAnalysis, MagicStick, 
  ArrowRight, ArrowLeft 
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

export default {
  name: 'QuestionGeneration',
  components: {
    Document,
    Loading,
    ChatDotRound,
    DataAnalysis,
    MagicStick,
    ArrowRight,
    ArrowLeft
  },
  setup() {
    const router = useRouter()
    const route = useRoute()
    
    const documentId = ref('')
    const filename = ref('')
    const currentStep = ref(1)
    const generatingQuestions = ref(false)
    const generationProgress = ref(0)
    const generationText = ref('')
    const currentGenerationStep = ref(0)
    const questionSet = ref(null)
    const selectedQuestions = ref([])
    const questionHistory = ref({}) // Step별 질문 히스토리
    
    const reportForm = reactive({
      reportType: 'executive_summary',
      customRequirements: '',
      outputOptions: ['charts', 'summary']
    })

    onMounted(() => {
      // URL 쿼리에서 문서 정보 가져오기
      documentId.value = route.query.documentId || ''
      filename.value = route.query.filename || ''
      
      if (!documentId.value) {
        ElMessage.error('문서 정보를 찾을 수 없습니다. 문서 업로드부터 다시 시작해주세요.')
        router.push('/upload')
      }
    })

    const proceedToNextStep = async () => {
      if (selectedQuestions.value.length === 0) {
        ElMessage.warning('다음 단계로 진행하려면 최소 1개 이상의 질문을 선택해주세요.')
        return
      }

      if (currentStep.value >= 5) {
        ElMessage.info('모든 Step이 완료되었습니다. 리포트 생성을 진행합니다.')
        proceedToReport()
        return
      }

      try {
        // 다음 Step 질문 생성
        const nextStep = currentStep.value + 1
        generatingQuestions.value = true
        generationProgress.value = 0
        generationText.value = `Step ${nextStep} 질문 생성 중...`
        currentGenerationStep.value = 0

        // 진행률 시뮬레이션
        const progressInterval = setInterval(() => {
          if (generationProgress.value < 90) {
            generationProgress.value += 10
            if (generationProgress.value < 30) {
              generationText.value = '문서 재분석 중...'
              currentGenerationStep.value = 0
            } else if (generationProgress.value < 60) {
              generationText.value = `Step ${nextStep} 질문 생성 중...`
              currentGenerationStep.value = 1
            } else if (generationProgress.value < 90) {
              generationText.value = '질문 우선순위 설정 중...'
              currentGenerationStep.value = 2
            }
          }
        }, 800)

        // 다음 Step API 호출
        const apiUrl = process.env.VUE_APP_API_URL ? `${process.env.VUE_APP_API_URL}/questions/${documentId.value}/next` : `/api/questions/${documentId.value}/next`
        const response = await axios.post(apiUrl, { current_step: currentStep.value })
        
        clearInterval(progressInterval)
        generationProgress.value = 100
        generationText.value = `Step ${nextStep} 질문 생성 완료!`
        currentGenerationStep.value = 3

        // 다음 Step으로 진행
        currentStep.value = nextStep
        questionSet.value = response.data
        selectedQuestions.value = []
        
        // 히스토리에 저장
        questionHistory.value[nextStep] = response.data

        ElMessage.success(`Step ${nextStep} 질문이 생성되었습니다! 원하는 질문을 선택해주세요.`)
        
      } catch (error) {
        console.error('다음 Step 진행 오류:', error)
        ElMessage.error('다음 단계 진행 중 오류가 발생했습니다. 다시 시도해주세요.')
      } finally {
        generatingQuestions.value = false
      }
    }

    const generateQuestions = async () => {
      // 첫 번째 Step부터 자동 시작
      currentStep.value = 1
      
      generatingQuestions.value = true
      generationProgress.value = 0
      generationText.value = '문서 내용 분석 중...'
      currentGenerationStep.value = 0

      try {
        // 질문 생성 진행률 시뮬레이션
        const progressInterval = setInterval(() => {
          if (generationProgress.value < 90) {
            generationProgress.value += 10
            
            if (generationProgress.value < 25) {
              generationText.value = '문서 내용 분석 중...'
              currentGenerationStep.value = 0
            } else if (generationProgress.value < 50) {
              generationText.value = '주요 토픽 추출 중...'
              currentGenerationStep.value = 1
            } else if (generationProgress.value < 75) {
              generationText.value = `Step ${currentStep.value} 질문 생성 중...`
              currentGenerationStep.value = 2
            } else if (generationProgress.value < 90) {
              generationText.value = '질문 우선순위 설정 중...'
              currentGenerationStep.value = 3
            }
          }
        }, 800)

        // 실제 백엔드 API 호출 (Step 1)
        const apiUrl = process.env.VUE_APP_API_URL ? `${process.env.VUE_APP_API_URL}/questions/${documentId.value}?step=1` : `/api/questions/${documentId.value}?step=1`
        const response = await axios.get(apiUrl)
        
        clearInterval(progressInterval)
        generationProgress.value = 100
        generationText.value = `Step ${currentStep.value} 질문 생성 완료!`
        currentGenerationStep.value = 3

        // 생성된 질문 세트 저장
        questionSet.value = response.data
        
        // 히스토리에 저장
        questionHistory.value[currentStep.value] = response.data

        // 에이전트 질문 생성 과정 로그 표시
        console.log(`Step ${currentStep.value} 질문 생성 완료:`, response.data)
        console.log(`에이전트가 생성한 질문 수:`, response.data.questions.length)
        console.log(`질문 세트 버전:`, response.data.version)
        console.log(`생성 시간:`, response.data.generated_at)

        ElMessage.success(`Step ${currentStep.value} 질문이 성공적으로 생성되었습니다! 원하는 질문을 선택해주세요.`)
        
      } catch (error) {
        console.error('질문 생성 오류:', error)
        ElMessage.error('질문 생성 중 오류가 발생했습니다. 다시 시도해주세요.')
      } finally {
        generatingQuestions.value = false
      }
    }

    const proceedToReport = () => {
      if (selectedQuestions.value.length === 0) {
        ElMessage.warning('리포트 생성을 위해 최소 1개 이상의 질문을 선택해주세요.')
        return
      }

      // 선택된 질문 정보와 리포트 설정을 다음 페이지로 전달
      const selectedQuestionData = questionSet.value.questions.filter(
        q => selectedQuestions.value.includes(q.question_id)
      )

      router.push({
        path: '/report',
        query: { 
          documentId: documentId.value,
          filename: filename.value,
          selectedQuestions: JSON.stringify(selectedQuestionData),
          reportType: reportForm.reportType,
          customRequirements: reportForm.customRequirements,
          outputOptions: JSON.stringify(reportForm.outputOptions)
        }
      })
    }

    const goBack = () => {
      router.push('/upload')
    }

    const formatDate = (date) => {
      return date.toLocaleString('ko-KR')
    }

    const getStepDescription = (step) => {
      const descriptions = {
        1: '기본 이해',
        2: '상세 분석',
        3: '집중 분석',
        4: '인사이트',
        5: '맞춤형'
      }
      return descriptions[step] || '기본'
    }

    const getStepDetailDescription = (step) => {
      const details = {
        1: '문서의 주요 내용과 핵심 메시지를 파악하는 기본적인 질문들을 생성합니다.',
        2: '주요 데이터, 통계, 구조 등에 대한 상세한 분석 질문을 생성합니다.',
        3: '특정 영역(엔티티, 방법론, 시장 등)에 집중한 분석 질문을 생성합니다.',
        4: '실행 가능한 인사이트와 권장사항을 도출하는 질문을 생성합니다.',
        5: '사용자 요구사항에 맞는 맞춤형 심화 질문을 생성합니다.'
      }
      return details[step] || '기본적인 질문을 생성합니다.'
    }

    const getStepTagType = (step) => {
      const types = {
        1: 'success',
        2: 'warning',
        3: 'info',
        4: 'danger',
        5: 'primary'
      }
      return types[step] || 'default'
    }

    const getQuestionCategories = (questions) => {
      const categories = [...new Set(questions.map(q => q.category))]
      return categories.join(', ')
    }

    const getAverageConfidence = (questions) => {
      if (questions.length === 0) return 0
      const total = questions.reduce((sum, q) => sum + q.confidence_score, 0)
      return Math.round((total / questions.length) * 100)
    }

    const formatDateTime = (timestamp) => {
      if (!timestamp) return 'N/A'
      return new Date(timestamp).toLocaleString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    }

    return {
      documentId,
      filename,
      currentStep,
      generatingQuestions,
      generationProgress,
      generationText,
      currentGenerationStep,
      questionSet,
      selectedQuestions,
      reportForm,
      generateQuestions,
      proceedToNextStep,
      proceedToReport,
      goBack,
      formatDate,
      getStepDescription,
      getStepDetailDescription,
      getStepTagType,
      getQuestionCategories,
      getAverageConfidence,
      formatDateTime
    }
  }
}
</script>

<style scoped>
.question-generation {
  padding: 20px 0;
}

.progress-card {
  margin-bottom: 20px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.document-info-card {
  margin-bottom: 20px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 1.2rem;
  font-weight: 600;
}

.question-count {
  margin-left: auto;
}

.document-details {
  margin: 20px 0;
}

.generation-card {
  margin-bottom: 20px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.generation-progress {
  text-align: center;
  padding: 20px;
}

.progress-text {
  margin: 20px 0;
  color: #606266;
  font-size: 1.1rem;
}

.generation-steps {
  margin-top: 30px;
  text-align: left;
}

.questions-card {
  margin-bottom: 20px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.questions-container {
  margin: 20px 0;
}

.questions-header {
  text-align: center;
  margin-bottom: 30px;
}

.questions-header h3 {
  color: #2c3e50;
  margin-bottom: 10px;
}

.questions-header p {
  color: #7f8c8d;
  margin: 0;
}

.questions-list {
  margin: 30px 0;
}

.question-item {
  margin-bottom: 20px;
  padding: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.question-item:hover {
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
}

.question-checkbox {
  width: 100%;
}

.question-content {
  margin-left: 10px;
}

.question-text {
  font-size: 1.1rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 10px;
  line-height: 1.5;
}

.question-meta {
  margin-bottom: 10px;
}

.question-meta .el-tag {
  margin-right: 8px;
}

.question-context {
  color: #7f8c8d;
  font-size: 0.9rem;
  font-style: italic;
  line-height: 1.4;
}

.selection-summary {
  margin: 30px 0;
}

.auto-step-card {
  margin-bottom: 20px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.auto-step-info {
  margin: 20px 0;
}

.current-step-display {
  margin-top: 20px;
  padding: 20px;
  background-color: #f0f9ff;
  border-radius: 12px;
  border-left: 4px solid #3b82f6;
}

.current-step-display h4 {
  color: #1e40af;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.current-step-display p {
  color: #374151;
  margin-bottom: 15px;
  line-height: 1.6;
}

.step-progress {
  margin-top: 15px;
}

.agent-process-card {
  margin-bottom: 20px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.agent-process-info {
  margin: 20px 0;
}

.agent-log-section {
  margin-top: 20px;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 12px;
  border-left: 4px solid #667eea;
}

.agent-log-section h4 {
  color: #2c3e50;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.log-content p {
  margin: 8px 0;
  color: #606266;
  line-height: 1.6;
}

.log-content strong {
  color: #2c3e50;
}

.report-type-card {
  margin-bottom: 20px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.report-type-selection {
  margin: 20px 0;
}

.action-buttons {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: 30px;
  flex-wrap: wrap;
}

/* 반응형 디자인 */
@media (max-width: 768px) {
  .action-buttons {
    flex-direction: column;
    align-items: center;
  }
  
  .question-item {
    padding: 15px;
  }
  
  .question-text {
    font-size: 1rem;
  }
}
</style>