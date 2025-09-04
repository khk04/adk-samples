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

        <!-- 리포트 생성 영역 -->
        <el-card class="report-card">
          <template #header>
            <div class="card-header">
              <i class="el-icon-document"></i>
              <span>리포트 생성</span>
            </div>
          </template>
          
          <div class="report-content">
            <div class="selected-questions">
              <h3>선택된 질문들</h3>
              <ul>
                <li v-for="(question, index) in selectedQuestions" :key="index">
                  {{ question }}
                </li>
              </ul>
            </div>
            
            <el-button 
              type="primary" 
              size="large" 
              @click="generateReport"
              :loading="generatingReport"
            >
              <i class="el-icon-magic-stick"></i>
              리포트 생성하기
            </el-button>
            
            <div v-if="reportContent" class="report-result">
              <h3>생성된 리포트</h3>
              <div class="report-preview">
                <pre>{{ reportContent }}</pre>
              </div>
              
              <div class="download-actions">
                <el-button 
                  type="success" 
                  size="large" 
                  @click="downloadReport('pdf')"
                  :loading="downloading === 'pdf'"
                >
                  <i class="el-icon-download"></i>
                  PDF 다운로드
                </el-button>
                
                <el-button 
                  type="info" 
                  size="large" 
                  @click="downloadReport('docx')"
                  :loading="downloading === 'docx'"
                >
                  <i class="el-icon-download"></i>
                  DOCX 다운로드
                </el-button>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
export default {
  name: 'ReportGeneration',
  data() {
    return {
      documentId: '',
      filename: '',
      selectedQuestions: [],
      generatingReport: false,
      reportContent: '',
      downloading: ''
    }
  },
  mounted() {
    // URL 쿼리에서 정보 가져오기
    this.documentId = this.$route.query.documentId || ''
    this.filename = this.$route.query.filename || ''
    
    try {
      this.selectedQuestions = JSON.parse(this.$route.query.selectedQuestions || '[]')
    } catch (error) {
      this.selectedQuestions = []
    }
    
    if (!this.documentId || this.selectedQuestions.length === 0) {
      this.$message.error('필요한 정보가 없습니다.')
      this.$router.push('/questions')
    }
  },
  methods: {
    async generateReport() {
      this.generatingReport = true
      
      try {
        // Mock 리포트 생성 (실제로는 API 호출)
        await new Promise(resolve => setTimeout(resolve, 3000))
        
        this.reportContent = `# 문서 분석 리포트

## 문서 정보
- 파일명: ${this.filename}
- 문서 ID: ${this.documentId}
- 생성일: ${new Date().toLocaleDateString('ko-KR')}

## 선택된 질문들
${this.selectedQuestions.map((q, i) => `${i + 1}. ${q}`).join('\n')}

## 분석 결과

### 1. 문서 개요
이 문서는 선택된 질문들을 바탕으로 분석되었습니다.

### 2. 주요 내용
- 문서의 핵심 내용을 분석한 결과
- 선택된 질문들에 대한 답변을 포함
- 구조화된 정보 제공

### 3. 결론
분석 결과를 종합하여 다음과 같은 결론을 도출할 수 있습니다.

## 권장사항
1. 추가적인 데이터 수집을 권장합니다
2. 정기적인 모니터링이 필요합니다
3. 관련 문서와의 비교 분석을 제안합니다

---
*이 리포트는 Document Question & Report Agent에 의해 자동 생성되었습니다.*`
        
        this.$message.success('리포트가 성공적으로 생성되었습니다!')
        
      } catch (error) {
        console.error('리포트 생성 오류:', error)
        this.$message.error('리포트 생성 중 오류가 발생했습니다.')
      } finally {
        this.generatingReport = false
      }
    },
    
    async downloadReport(format) {
      this.downloading = format
      
      try {
        // Mock 다운로드 (실제로는 API 호출)
        await new Promise(resolve => setTimeout(resolve, 2000))
        
        // 간단한 파일 다운로드 시뮬레이션
        const blob = new Blob([this.reportContent], { type: 'text/plain' })
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `report_${this.filename}_${new Date().getTime()}.${format}`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        
        this.$message.success(`${format.toUpperCase()} 형식으로 리포트가 다운로드되었습니다!`)
        
      } catch (error) {
        console.error('다운로드 오류:', error)
        this.$message.error('다운로드 중 오류가 발생했습니다.')
      } finally {
        this.downloading = ''
      }
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

.report-card {
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

.report-content {
  padding: 20px;
}

.selected-questions {
  margin-bottom: 30px;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.selected-questions ul {
  list-style: none;
  padding: 0;
}

.selected-questions li {
  padding: 8px 0;
  border-bottom: 1px solid #e4e7ed;
}

.selected-questions li:last-child {
  border-bottom: none;
}

.report-result {
  margin-top: 30px;
}

.report-preview {
  margin: 20px 0;
  padding: 20px;
  background-color: #f9f9f9;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.report-preview pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', monospace;
  line-height: 1.6;
}

.download-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: 30px;
}

/* 반응형 디자인 */
@media (max-width: 768px) {
  .download-actions {
    flex-direction: column;
    align-items: center;
  }
}
</style>