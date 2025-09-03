<template>
  <div class="report-generation">
    <el-row :gutter="20" justify="center">
      <el-col :span="20">
        <!-- 진행 단계 표시 -->
        <el-card class="progress-card">
          <el-steps :active="3" finish-status="success" align-center>
            <el-step title="문서 업로드" description="분석할 문서를 업로드합니다" />
            <el-step title="질문 생성" description="AI가 문서 내용을 분석하여 질문을 생성합니다" />
            <el-step title="질문 선택" description="원하는 분석 내용을 선택합니다" />
            <el-step title="리포트 생성" description="선택된 내용을 바탕으로 리포트를 생성합니다" />
            <el-step title="다운로드" description="완성된 리포트를 다운로드합니다" />
          </el-steps>
        </el-card>

        <!-- 선택된 질문 요약 -->
        <el-card class="summary-card">
          <template #header>
            <div class="card-header">
              <el-icon><ChatDotRound /></el-icon>
              <span>선택된 분석 내용</span>
            </div>
          </template>
          
          <div class="selected-questions">
            <el-descriptions title="분석 설정" :column="2" border>
              <el-descriptions-item label="문서 ID">{{ documentId }}</el-descriptions-item>
              <el-descriptions-item label="파일명">{{ filename }}</el-descriptions-item>
              <el-descriptions-item label="리포트 유형">
                <el-tag type="primary">{{ getReportTypeLabel(reportType) }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="선택된 질문 수">
                <el-tag type="success">{{ selectedQuestions.length }}개</el-tag>
              </el-descriptions-item>
            </el-descriptions>
            
            <div class="questions-preview">
              <h4>📋 선택된 질문 목록</h4>
              <el-timeline>
                <el-timeline-item
                  v-for="(question, index) in selectedQuestions"
                  :key="question.question_id"
                  :timestamp="`질문 ${index + 1}`"
                  placement="top"
                >
                  <el-card class="question-preview-card">
                    <div class="question-preview-content">
                      <div class="question-text">{{ question.question }}</div>
                      <div class="question-meta">
                        <el-tag size="small" type="primary">{{ question.category }}</el-tag>
                        <el-tag size="small" type="warning">우선순위: {{ question.priority }}</el-tag>
                      </div>
                    </div>
                  </el-card>
                </el-timeline-item>
              </el-timeline>
            </div>
          </div>
        </el-card>

        <!-- 리포트 생성 진행 상황 -->
        <el-card v-if="generatingReport" class="generation-card">
          <template #header>
            <div class="card-header">
              <el-icon><Loading /></el-icon>
              <span>리포트 생성 중...</span>
            </div>
          </template>
          
          <div class="generation-progress">
            <el-progress 
              :percentage="generationProgress" 
              :status="generationProgress === 100 ? 'success' : ''"
              :stroke-width="20"
            />
            <p class="progress-text">{{ progressText }}</p>
            
            <div class="generation-steps">
              <el-steps :active="currentGenerationStep" direction="vertical" size="small">
                <el-step title="컨텍스트 분석" description="선택된 질문과 문서 내용을 분석합니다" />
                <el-step title="리포트 아웃라인 생성" description="리포트의 구조와 목차를 설계합니다" />
                <el-step title="내용 생성" description="AI가 분석 내용을 바탕으로 리포트를 작성합니다" />
                <el-step title="품질 검증" description="생성된 리포트의 품질을 검증하고 최적화합니다" />
                <el-step title="최종 완성" description="리포트를 최종 형태로 완성합니다" />
              </el-steps>
            </div>
          </div>
        </el-card>

        <!-- 생성된 리포트 결과 -->
        <el-card v-if="finalReport && !generatingReport" class="result-card">
          <template #header>
            <div class="card-header">
              <el-icon><Document /></el-icon>
              <span>리포트 생성 완료</span>
              <el-tag type="success">완성</el-tag>
            </div>
          </template>
          
          <div class="report-result">
            <el-alert
              title="리포트 생성이 완료되었습니다!"
              type="success"
              description="선택한 내용을 바탕으로 전문적인 리포트가 생성되었습니다. 다양한 형식으로 다운로드할 수 있습니다."
              show-icon
              :closable="false"
              class="success-alert"
            />
            
            <div class="report-details">
              <el-descriptions title="리포트 정보" :column="2" border>
                <el-descriptions-item label="리포트 ID">{{ finalReport.report_id }}</el-descriptions-item>
                <el-descriptions-item label="생성 시간">{{ formatDate(finalReport.generated_at) }}</el-descriptions-item>
                <el-descriptions-item label="제목">{{ finalReport.title }}</el-descriptions-item>
                <el-descriptions-item label="상태">
                  <el-tag type="success">{{ finalReport.status }}</el-tag>
                </el-descriptions-item>
              </el-descriptions>
            </div>
            
            <div class="report-preview">
              <h4>📄 리포트 미리보기</h4>
              <div class="preview-content">
                <div class="executive-summary">
                  <h5>📋 집행 요약</h5>
                  <p>{{ finalReport.executive_summary }}</p>
                </div>
                
                <div class="key-findings">
                  <h5>🔍 주요 발견사항</h5>
                  <ul>
                    <li v-for="(finding, index) in finalReport.findings" :key="index">
                      {{ finding }}
                    </li>
                  </ul>
                </div>
                
                <div class="recommendations">
                  <h5>💡 권장사항</h5>
                  <ul>
                    <li v-for="(rec, index) in finalReport.recommendations" :key="index">
                      {{ rec }}
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 다운로드 옵션 -->
        <el-card v-if="finalReport && !generatingReport" class="download-card">
          <template #header>
            <div class="card-header">
              <el-icon><Download /></el-icon>
              <span>리포트 다운로드</span>
            </div>
          </template>
          
          <div class="download-options">
            <h4>📥 다운로드 형식 선택</h4>
            <p>원하는 형식으로 리포트를 다운로드할 수 있습니다.</p>
            
            <div class="format-buttons">
              <el-button 
                type="primary" 
                size="large" 
                @click="downloadReport('pdf')"
                :loading="downloading === 'pdf'"
              >
                <el-icon><Document /></el-icon>
                PDF 다운로드
              </el-button>
              
              <el-button 
                type="success" 
                size="large" 
                @click="downloadReport('docx')"
                :loading="downloading === 'docx'"
              >
                <el-icon><Document /></el-icon>
                Word 문서
              </el-button>
              
              <el-button 
                type="warning" 
                size="large" 
                @click="downloadReport('html')"
                :loading="downloading === 'html'"
              >
                <el-icon><Monitor /></el-icon>
                HTML 웹페이지
              </el-button>
              
              <el-button 
                type="info" 
                size="large" 
                @click="downloadReport('pptx')"
                :loading="downloading === 'pptx'"
              >
                <el-icon><Present /></el-icon>
                PowerPoint
              </el-button>
            </div>
            
            <div class="download-note">
              <el-alert
                title="다운로드 안내"
                type="info"
                description="리포트는 고품질로 생성되었으며, 선택한 형식에 따라 최적화되어 제공됩니다."
                show-icon
                :closable="false"
              />
            </div>
          </div>
        </el-card>

        <!-- 액션 버튼 -->
        <div class="action-buttons">
          <el-button 
            v-if="!finalReport"
            type="primary" 
            size="large" 
            @click="generateReport"
            :loading="generatingReport"
            :disabled="!selectedQuestions.length"
          >
            <el-icon><MagicStick /></el-icon>
            리포트 생성 시작
          </el-button>
          
          <el-button 
            v-if="finalReport"
            type="success" 
            size="large" 
            @click="startNewWorkflow"
          >
            <el-icon><Refresh /></el-icon>
            새로운 문서로 시작
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
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { 
  ChatDotRound, Loading, Document, Download, Monitor, Present,
  MagicStick, Refresh, ArrowLeft 
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

export default {
  name: 'ReportGeneration',
  components: {
    ChatDotRound,
    Loading,
    Document,
    Download,
    Monitor,
    Present,
    MagicStick,
    Refresh,
    ArrowLeft
  },
  setup() {
    const router = useRouter()
    const route = useRoute()
    
    const documentId = ref('')
    const filename = ref('')
    const reportType = ref('')
    const selectedQuestions = ref([])
    const customRequirements = ref('')
    const outputOptions = ref([])
    
    const generatingReport = ref(false)
    const generationProgress = ref(0)
    const progressText = ref('')
    const currentGenerationStep = ref(0)
    const finalReport = ref(null)
    const downloading = ref('')

    onMounted(() => {
      // URL 쿼리에서 정보 가져오기
      documentId.value = route.query.documentId || ''
      filename.value = route.query.filename || ''
      reportType.value = route.query.reportType || 'executive_summary'
      
      try {
        selectedQuestions.value = JSON.parse(route.query.selectedQuestions || '[]')
        customRequirements.value = route.query.customRequirements || ''
        outputOptions.value = JSON.parse(route.query.outputOptions || '[]')
      } catch (error) {
        console.error('쿼리 파라미터 파싱 오류:', error)
        ElMessage.error('페이지 로딩 중 오류가 발생했습니다.')
        router.push('/questions')
      }
      
      if (!documentId.value || !selectedQuestions.value.length) {
        ElMessage.error('필요한 정보가 누락되었습니다. 이전 단계로 돌아가주세요.')
        router.push('/questions')
      }
    })

    const generateReport = async () => {
      generatingReport.value = true
      generationProgress.value = 0
      progressText.value = '컨텍스트 분석 중...'
      currentGenerationStep.value = 0

      try {
        // 리포트 생성 진행률 시뮬레이션
        const progressInterval = setInterval(() => {
          if (generationProgress.value < 90) {
            generationProgress.value += 10
            
            if (generationProgress.value < 20) {
              progressText.value = '컨텍스트 분석 중...'
              currentGenerationStep.value = 0
            } else if (generationProgress.value < 40) {
              progressText.value = '리포트 아웃라인 생성 중...'
              currentGenerationStep.value = 1
            } else if (generationProgress.value < 60) {
              progressText.value = '내용 생성 중...'
              currentGenerationStep.value = 2
            } else if (generationProgress.value < 80) {
              progressText.value = '품질 검증 중...'
              currentGenerationStep.value = 3
            } else if (generationProgress.value < 90) {
              progressText.value = '최종 완성 중...'
              currentGenerationStep.value = 4
            }
          }
        }, 1000)

        // 실제 API 호출 (시뮬레이션)
        await new Promise(resolve => setTimeout(resolve, 6000))
        
        clearInterval(progressInterval)
        generationProgress.value = 100
        progressText.value = '리포트 생성 완료!'
        currentGenerationStep.value = 4

        // 생성된 리포트 (시뮬레이션 데이터)
        finalReport.value = {
          report_id: 'rpt_' + Date.now(),
          draft_id: 'draft_' + Date.now(),
          title: `${getReportTypeLabel(reportType.value)} 리포트`,
          content: '선택된 질문들을 바탕으로 생성된 상세한 리포트 내용...',
          executive_summary: '이 리포트는 선택된 질문들을 바탕으로 문서를 분석한 결과입니다. 주요 발견사항과 권장사항을 포함하여 실무에 활용할 수 있는 인사이트를 제공합니다.',
          methodology: 'AI 기반 문서 분석 및 질문 생성 방법론을 사용하여 리포트를 작성했습니다.',
          findings: [
            '문서의 주요 내용과 핵심 메시지를 파악했습니다.',
            '주요 데이터와 통계 정보를 분석했습니다.',
            '결론과 권장사항을 도출했습니다.',
            '관련 이해관계자와 조직을 식별했습니다.',
            '분석 방법론과 접근법을 정리했습니다.'
          ],
          conclusions: [
            '문서는 체계적으로 구성되어 있으며 명확한 메시지를 전달합니다.',
            '데이터 기반의 분석 결과가 제시되어 신뢰성이 높습니다.',
            '실행 가능한 권장사항이 포함되어 실무 활용도가 높습니다.'
          ],
          recommendations: [
            '제시된 방법론을 다른 유사 문서 분석에 적용해보세요.',
            '정기적인 업데이트를 통해 최신 정보를 반영하세요.',
            '팀 내 공유를 통해 조직 전체의 인사이트를 향상시키세요.'
          ],
          appendices: [
            {
              title: '원본 문서 정보',
              content: `문서 ID: ${documentId.value}`,
              type: 'metadata'
            }
          ],
          generated_at: new Date(),
          status: 'final'
        }

        ElMessage.success('리포트 생성이 완료되었습니다!')
        
      } catch (error) {
        console.error('리포트 생성 오류:', error)
        ElMessage.error('리포트 생성 중 오류가 발생했습니다. 다시 시도해주세요.')
      } finally {
        generatingReport.value = false
      }
    }

    const downloadReport = async (format) => {
      downloading.value = format
      
      try {
        // 다운로드 시뮬레이션
        await new Promise(resolve => setTimeout(resolve, 2000))
        
        // 실제 다운로드 로직 (시뮬레이션)
        const link = document.createElement('a')
        link.href = `data:text/plain;charset=utf-8,${encodeURIComponent('리포트 내용')}`
        link.download = `${finalReport.value.title}_${format}.${format}`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        
        ElMessage.success(`${format.toUpperCase()} 형식으로 리포트가 다운로드되었습니다!`)
        
      } catch (error) {
        console.error('다운로드 오류:', error)
        ElMessage.error('다운로드 중 오류가 발생했습니다.')
      } finally {
        downloading.value = ''
      }
    }

    const startNewWorkflow = () => {
      ElMessageBox.confirm(
        '새로운 문서로 작업을 시작하시겠습니까?',
        '새로운 작업 시작',
        {
          confirmButtonText: '시작',
          cancelButtonText: '취소',
          type: 'info'
        }
      ).then(() => {
        router.push('/upload')
      })
    }

    const goBack = () => {
      router.push('/questions')
    }

    const getReportTypeLabel = (type) => {
      const labels = {
        'executive_summary': '집행 요약',
        'technical_analysis': '기술 분석',
        'market_research': '시장 조사',
        'financial_report': '재무 보고서',
        'comparative_analysis': '비교 분석',
        'recommendation': '권장사항',
        'custom': '맞춤형'
      }
      return labels[type] || type
    }

    const formatDate = (date) => {
      return new Date(date).toLocaleString('ko-KR')
    }

    return {
      documentId,
      filename,
      reportType,
      selectedQuestions,
      customRequirements,
      outputOptions,
      generatingReport,
      generationProgress,
      progressText,
      currentGenerationStep,
      finalReport,
      downloading,
      generateReport,
      downloadReport,
      startNewWorkflow,
      goBack,
      getReportTypeLabel,
      formatDate
    }
  }
}
</script>

<style scoped>
.report-generation {
  padding: 20px 0;
}

.progress-card {
  margin-bottom: 20px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.summary-card {
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

.selected-questions {
  margin: 20px 0;
}

.questions-preview {
  margin-top: 30px;
}

.questions-preview h4 {
  color: #2c3e50;
  margin-bottom: 20px;
  text-align: center;
}

.question-preview-card {
  margin-bottom: 10px;
  border-radius: 8px;
}

.question-preview-content {
  padding: 10px;
}

.question-text {
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 10px;
  line-height: 1.4;
}

.question-meta .el-tag {
  margin-right: 8px;
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

.result-card {
  margin-bottom: 20px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.report-result {
  margin: 20px 0;
}

.success-alert {
  margin-bottom: 30px;
}

.report-details {
  margin: 30px 0;
}

.report-preview {
  margin: 30px 0;
}

.report-preview h4 {
  color: #2c3e50;
  margin-bottom: 20px;
  text-align: center;
}

.preview-content {
  background-color: #f8f9fa;
  padding: 20px;
  border-radius: 12px;
}

.preview-content h5 {
  color: #2c3e50;
  margin: 20px 0 10px 0;
  font-weight: 600;
}

.preview-content h5:first-child {
  margin-top: 0;
}

.preview-content p,
.preview-content ul {
  color: #606266;
  line-height: 1.6;
  margin: 0;
}

.preview-content ul {
  padding-left: 20px;
}

.preview-content li {
  margin-bottom: 8px;
}

.download-card {
  margin-bottom: 20px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.download-options {
  text-align: center;
  margin: 20px 0;
}

.download-options h4 {
  color: #2c3e50;
  margin-bottom: 10px;
  font-weight: 600;
}

.download-options p {
  color: #7f8c8d;
  margin-bottom: 30px;
}

.format-buttons {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-bottom: 30px;
  flex-wrap: wrap;
}

.download-note {
  margin-top: 20px;
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
  .format-buttons {
    flex-direction: column;
    align-items: center;
  }
  
  .action-buttons {
    flex-direction: column;
    align-items: center;
  }
  
  .preview-content {
    padding: 15px;
  }
}
</style>