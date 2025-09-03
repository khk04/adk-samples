<template>
  <div class="question-generation">
    <el-card class="question-card">
      <template #header>
        <div class="card-header">
          <span>질문 생성</span>
          <el-button @click="$router.push('/')" type="text" size="small">
            <el-icon><Back /></el-icon>
            홈으로 돌아가기
          </el-button>
        </div>
      </template>

      <!-- 문서 선택 -->
      <div v-if="!selectedDocument" class="document-selection">
        <h3>문서를 선택해주세요</h3>
        <el-select 
          v-model="selectedDocumentId" 
          placeholder="업로드된 문서를 선택하세요"
          class="document-select"
          @change="onDocumentSelect"
        >
          <el-option
            v-for="doc in availableDocuments"
            :key="doc.document_id"
            :label="doc.filename"
            :value="doc.document_id"
          />
        </el-select>
      </div>

      <!-- 질문 생성 영역 -->
      <div v-if="selectedDocument" class="question-area">
        <div class="document-info">
          <el-alert
            :title="`선택된 문서: ${selectedDocument.filename}`"
            type="info"
            :closable="false"
            show-icon
          />
        </div>

        <!-- 질문 생성 버튼 -->
        <div class="generate-actions">
          <el-button 
            type="primary" 
            size="large" 
            @click="generateQuestions"
            :loading="generating"
            :disabled="!selectedDocumentId"
          >
            <el-icon><QuestionFilled /></el-icon>
            {{ generating ? '질문 생성 중...' : '질문 생성하기' }}
          </el-button>
          <el-button 
            @click="regenerateQuestions" 
            size="large"
            :disabled="!hasQuestions"
          >
            <el-icon><Refresh /></el-icon>
            질문 재생성
          </el-button>
        </div>

        <!-- 질문 목록 -->
        <div v-if="questions.length > 0" class="questions-list">
          <h3>생성된 질문들</h3>
          <p class="question-instruction">
            리포트에 포함할 질문들을 선택해주세요. (복수 선택 가능)
          </p>
          
          <el-checkbox-group v-model="selectedQuestions" class="question-checkboxes">
            <el-card 
              v-for="(question, index) in questions" 
              :key="index"
              class="question-item"
              :class="{ 'selected': selectedQuestions.includes(index) }"
            >
              <el-checkbox :label="index" class="question-checkbox">
                <div class="question-content">
                  <h4>{{ question.text }}</h4>
                  <p class="question-category">
                    <el-tag size="small" :type="getCategoryType(question.category)">
                      {{ question.category }}
                    </el-tag>
                  </p>
                  <p class="question-description">{{ question.description }}</p>
                </div>
              </el-checkbox>
            </el-card>
          </el-checkbox-group>

          <!-- 선택된 질문 요약 -->
          <div v-if="selectedQuestions.length > 0" class="selected-summary">
            <el-alert
              :title="`${selectedQuestions.length}개 질문이 선택되었습니다`"
              type="success"
              :closable="false"
              show-icon
            />
          </div>

          <!-- 리포트 생성 버튼 -->
          <div class="report-actions">
            <el-button 
              type="success" 
              size="large" 
              @click="goToReportGeneration"
              :disabled="selectedQuestions.length === 0"
            >
              <el-icon><DocumentCopy /></el-icon>
              선택된 질문으로 리포트 생성
            </el-button>
          </div>
        </div>

        <!-- 질문 재생성 피드백 -->
        <el-dialog
          v-model="feedbackDialogVisible"
          title="질문 재생성 피드백"
          width="500px"
        >
          <el-form :model="feedbackForm" label-width="100px">
            <el-form-item label="피드백">
              <el-input
                v-model="feedbackForm.text"
                type="textarea"
                :rows="4"
                placeholder="현재 질문들에 대한 피드백을 입력해주세요. 예: 더 구체적인 질문이 필요합니다, 다른 관점의 질문을 원합니다 등"
              />
            </el-form-item>
          </el-form>
          <template #footer>
            <span class="dialog-footer">
              <el-button @click="feedbackDialogVisible = false">취소</el-button>
              <el-button type="primary" @click="submitFeedback">피드백 제출</el-button>
            </span>
          </template>
        </el-dialog>
      </div>
    </el-card>
  </div>
</template>

<script>
import { 
  Back, 
  QuestionFilled, 
  Refresh, 
  DocumentCopy 
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

export default {
  name: 'QuestionGeneration',
  components: {
    Back,
    QuestionFilled,
    Refresh,
    DocumentCopy
  },
  data() {
    return {
      selectedDocumentId: '',
      selectedDocument: null,
      availableDocuments: [],
      questions: [],
      selectedQuestions: [],
      generating: false,
      hasQuestions: false,
      feedbackDialogVisible: false,
      feedbackForm: {
        text: ''
      }
    }
  },
  mounted() {
    this.loadAvailableDocuments()
    // URL 쿼리에서 document_id 확인
    const documentId = this.$route.query.document_id
    if (documentId) {
      this.selectedDocumentId = documentId
      this.onDocumentSelect(documentId)
    }
  },
  methods: {
    async loadAvailableDocuments() {
      try {
        // 실제로는 API에서 업로드된 문서 목록을 가져와야 함
        // 현재는 로컬 스토리지에서 가져오는 것으로 가정
        const documents = JSON.parse(localStorage.getItem('uploadedDocuments') || '[]')
        this.availableDocuments = documents
      } catch (error) {
        console.error('문서 목록 로드 실패:', error)
      }
    },

    onDocumentSelect(documentId) {
      this.selectedDocument = this.availableDocuments.find(doc => doc.document_id === documentId)
      this.questions = []
      this.selectedQuestions = []
      this.hasQuestions = false
    },

    async generateQuestions() {
      if (!this.selectedDocumentId) {
        ElMessage.warning('문서를 선택해주세요.')
        return
      }

      this.generating = true
      try {
        const apiUrl = process.env.VUE_APP_API_URL ? `${process.env.VUE_APP_API_URL}/questions/${this.selectedDocumentId}` : `/api/questions/${this.selectedDocumentId}`
        const response = await axios.get(apiUrl)
        
        if (response.data && response.data.questions) {
          this.questions = response.data.questions
          this.hasQuestions = true
          this.selectedQuestions = []
          ElMessage.success('질문이 성공적으로 생성되었습니다!')
        } else {
          ElMessage.warning('질문을 생성할 수 없습니다.')
        }
      } catch (error) {
        console.error('질문 생성 실패:', error)
        ElMessage.error('질문 생성에 실패했습니다. 다시 시도해주세요.')
      } finally {
        this.generating = false
      }
    },

    async regenerateQuestions() {
      if (!this.selectedDocumentId) {
        ElMessage.warning('문서를 선택해주세요.')
        return
      }

      this.feedbackDialogVisible = true
    },

    async submitFeedback() {
      if (!this.feedbackForm.text.trim()) {
        ElMessage.warning('피드백을 입력해주세요.')
        return
      }

      try {
        const apiUrl = process.env.VUE_APP_API_URL ? `${process.env.VUE_APP_API_URL}/questions/${this.selectedDocumentId}/regenerate` : `/api/questions/${this.selectedDocumentId}/regenerate`
        const response = await axios.post(
          apiUrl,
          { feedback: this.feedbackForm.text }
        )

        if (response.data && response.data.questions) {
          this.questions = response.data.questions
          this.selectedQuestions = []
          this.feedbackForm.text = ''
          this.feedbackDialogVisible = false
          ElMessage.success('새로운 질문이 생성되었습니다!')
        }
      } catch (error) {
        console.error('질문 재생성 실패:', error)
        ElMessage.error('질문 재생성에 실패했습니다.')
      }
    },

    goToReportGeneration() {
      if (this.selectedQuestions.length === 0) {
        ElMessage.warning('리포트에 포함할 질문을 선택해주세요.')
        return
      }

      // 선택된 질문 정보를 전달
      const selectedQuestionData = this.selectedQuestions.map(index => this.questions[index])
      
      this.$router.push({
        path: '/report',
        query: { 
          document_id: this.selectedDocumentId,
          questions: JSON.stringify(selectedQuestionData)
        }
      })
    },

    getCategoryType(category) {
      const typeMap = {
        '일반': '',
        '분석': 'primary',
        '평가': 'warning',
        '예측': 'success',
        '비교': 'info'
      }
      return typeMap[category] || ''
    }
  }
}
</script>

<style scoped>
.question-generation {
  max-width: 1000px;
  margin: 0 auto;
}

.question-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.document-selection {
  text-align: center;
  padding: 40px 20px;
}

.document-selection h3 {
  margin-bottom: 20px;
  color: #2c3e50;
}

.document-select {
  width: 100%;
  max-width: 400px;
}

.document-info {
  margin-bottom: 20px;
}

.generate-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-bottom: 30px;
}

.questions-list h3 {
  margin-bottom: 15px;
  color: #2c3e50;
  border-bottom: 2px solid #409EFF;
  padding-bottom: 10px;
}

.question-instruction {
  margin-bottom: 20px;
  color: #606266;
  font-size: 14px;
}

.question-checkboxes {
  display: grid;
  gap: 15px;
  margin-bottom: 30px;
}

.question-item {
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.question-item:hover {
  border-color: #409EFF;
}

.question-item.selected {
  border-color: #67C23A;
  background-color: #f0f9ff;
}

.question-checkbox {
  width: 100%;
}

.question-content h4 {
  margin: 0 0 10px 0;
  color: #2c3e50;
  font-size: 16px;
}

.question-category {
  margin: 0 0 10px 0;
}

.question-description {
  margin: 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

.selected-summary {
  margin-bottom: 20px;
}

.report-actions {
  text-align: center;
}

@media (max-width: 768px) {
  .generate-actions {
    flex-direction: column;
  }
  
  .generate-actions .el-button {
    width: 100%;
  }
}
</style>