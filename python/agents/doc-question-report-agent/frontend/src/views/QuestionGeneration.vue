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

        <!-- 질문 생성 영역 -->
        <el-card class="question-card">
          <template #header>
            <div class="card-header">
              <i class="el-icon-chat-dot-round"></i>
              <span>질문 생성</span>
            </div>
          </template>
          
          <div class="question-content">
            <el-button 
              type="primary" 
              size="large" 
              @click="generateQuestions"
              :loading="generating"
            >
              <i class="el-icon-magic-stick"></i>
              질문 생성하기
            </el-button>
            
            <div v-if="questions.length > 0" class="questions-section">
              <h3>생성된 질문들</h3>
              <el-checkbox-group v-model="selectedQuestions">
                <el-checkbox 
                  v-for="(question, index) in questions" 
                  :key="index"
                  :label="question.question_text"
                  class="question-item"
                >
                  {{ question.question_text }}
                </el-checkbox>
              </el-checkbox-group>
              
              <div class="next-step">
                <el-button 
                  type="success" 
                  size="large" 
                  @click="proceedToReport"
                  :disabled="selectedQuestions.length === 0"
                >
                  <i class="el-icon-arrow-right"></i>
                  다음 단계: 리포트 생성
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
  name: 'QuestionGeneration',
  data() {
    return {
      documentId: '',
      filename: '',
      generating: false,
      questions: [],
      selectedQuestions: []
    }
  },
  mounted() {
    // URL 쿼리에서 문서 정보 가져오기
    this.documentId = this.$route.query.documentId || ''
    this.filename = this.$route.query.filename || ''
    
    if (!this.documentId) {
      this.$message.error('문서 정보가 없습니다.')
      this.$router.push('/upload')
    }
  },
  methods: {
    async generateQuestions() {
      this.generating = true
      
      try {
        // Mock 질문 생성 (실제로는 API 호출)
        await new Promise(resolve => setTimeout(resolve, 2000))
        
        this.questions = [
          {
            question_text: '이 문서의 주요 목적은 무엇인가요?',
            category: 'general',
            priority: 1
          },
          {
            question_text: '문서에서 언급된 핵심 개념은 무엇인가요?',
            category: 'analysis',
            priority: 2
          },
          {
            question_text: '문서의 결론이나 권장사항은 무엇인가요?',
            category: 'conclusion',
            priority: 3
          }
        ]
        
        this.$message.success('질문이 성공적으로 생성되었습니다!')
        
      } catch (error) {
        console.error('질문 생성 오류:', error)
        this.$message.error('질문 생성 중 오류가 발생했습니다.')
      } finally {
        this.generating = false
      }
    },
    
    proceedToReport() {
      if (this.selectedQuestions.length === 0) {
        this.$message.warning('최소 하나의 질문을 선택해주세요.')
        return
      }
      
      this.$router.push({
        path: '/report',
        query: {
          documentId: this.documentId,
          filename: this.filename,
          selectedQuestions: JSON.stringify(this.selectedQuestions)
        }
      })
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

.question-card {
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

.question-content {
  text-align: center;
  padding: 20px;
}

.questions-section {
  margin-top: 30px;
  text-align: left;
}

.question-item {
  display: block;
  margin: 15px 0;
  padding: 10px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background-color: #f9f9f9;
}

.next-step {
  text-align: center;
  margin-top: 30px;
}
</style>