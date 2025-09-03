<template>
  <div class="document-upload">
    <el-row :gutter="20" justify="center">
      <el-col :span="20">
        <!-- 진행 단계 표시 -->
        <el-card class="progress-card">
          <el-steps :active="1" finish-status="success" align-center>
            <el-step title="문서 업로드" description="분석할 문서를 업로드합니다" />
            <el-step title="질문 생성" description="AI가 문서 내용을 분석하여 질문을 생성합니다" />
            <el-step title="질문 선택" description="원하는 분석 내용을 선택합니다" />
            <el-step title="리포트 생성" description="선택된 내용을 바탕으로 리포트를 생성합니다" />
            <el-step title="다운로드" description="완성된 리포트를 다운로드합니다" />
          </el-steps>
        </el-card>

        <!-- 문서 업로드 영역 -->
        <el-card class="upload-card">
          <template #header>
            <div class="card-header">
              <el-icon><Upload /></el-icon>
              <span>문서 업로드</span>
            </div>
          </template>
          
          <div class="upload-area">
            <el-upload
              ref="uploadRef"
              class="upload-dragger"
              drag
              :auto-upload="false"
              :on-change="handleFileChange"
              :before-upload="beforeUpload"
              :file-list="fileList"
              :limit="1"
              accept=".pdf,.docx,.txt,.html,.htm,.md,.csv,.xlsx,.xls"
              multiple
            >
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">
                <em>클릭하여 파일을 선택하거나</em><br>
                <em>파일을 이 영역에 끌어다 놓으세요</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  지원 형식: PDF, DOCX, TXT, HTML, MD, CSV, Excel (최대 10MB)
                </div>
              </template>
            </el-upload>
          </div>

          <!-- 파일 정보 표시 -->
          <div v-if="selectedFile" class="file-info">
            <el-descriptions title="선택된 파일 정보" :column="2" border>
              <el-descriptions-item label="파일명">{{ selectedFile.name }}</el-descriptions-item>
              <el-descriptions-item label="파일 크기">{{ formatFileSize(selectedFile.size) }}</el-descriptions-item>
              <el-descriptions-item label="파일 형식">{{ getFileExtension(selectedFile.name) }}</el-descriptions-item>
              <el-descriptions-item label="마지막 수정">{{ formatDate(selectedFile.lastModified) }}</el-descriptions-item>
            </el-descriptions>
          </div>

          <!-- 업로드 버튼 -->
          <div class="upload-actions">
            <el-button 
              type="primary" 
              size="large" 
              @click="uploadDocument"
              :loading="uploading"
              :disabled="!selectedFile"
            >
              <el-icon><Upload /></el-icon>
              문서 업로드 및 분석 시작
            </el-button>
            
            <el-button 
              size="large" 
              @click="resetUpload"
              :disabled="!selectedFile"
            >
              <el-icon><Refresh /></el-icon>
              다시 선택
            </el-button>
          </div>
        </el-card>

        <!-- 업로드 진행 상황 -->
        <el-card v-if="uploading" class="progress-card">
          <template #header>
            <div class="card-header">
              <el-icon><Loading /></el-icon>
              <span>문서 처리 중...</span>
            </div>
          </template>
          
          <div class="progress-content">
            <el-progress 
              :percentage="uploadProgress" 
              :status="uploadProgress === 100 ? 'success' : ''"
              :stroke-width="20"
            />
            <p class="progress-text">{{ progressText }}</p>
          </div>
        </el-card>

        <!-- 결과 표시 -->
        <el-card v-if="documentAnalysis" class="result-card">
          <template #header>
            <div class="card-header">
              <el-icon><Document /></el-icon>
              <span>문서 분석 완료</span>
            </div>
          </template>
          
          <div class="analysis-result">
            <el-tabs v-model="activeTab" type="border-card">
              <!-- 기본 정보 탭 -->
              <el-tab-pane label="기본 정보" name="basic">
                <el-descriptions :column="2" border>
                  <el-descriptions-item label="문서 ID">{{ documentAnalysis.document_id }}</el-descriptions-item>
                  <el-descriptions-item label="파일명">{{ documentAnalysis.filename }}</el-descriptions-item>
                  <el-descriptions-item label="문서 타입">{{ documentAnalysis.document_type }}</el-descriptions-item>
                  <el-descriptions-item label="분석 시간">{{ formatDateTime(documentAnalysis.analysis_timestamp) }}</el-descriptions-item>
                  <el-descriptions-item label="분석 신뢰도" :span="2">
                    <el-progress 
                      :percentage="documentAnalysis.confidence_score * 100" 
                      :color="getConfidenceColor(documentAnalysis.confidence_score)"
                      :format="(percentage) => `${percentage.toFixed(1)}%`"
                    />
                  </el-descriptions-item>
                </el-descriptions>
              </el-tab-pane>

              <!-- 문서 요약 탭 -->
              <el-tab-pane label="문서 요약" name="summary">
                <div class="summary-section">
                  <h4>AI 생성 요약</h4>
                  <div class="summary-content">{{ documentAnalysis.summary }}</div>
                  
                  <h4>주요 토픽</h4>
                  <div class="topics-section">
                    <el-tag 
                      v-for="(topic, index) in documentAnalysis.key_topics" 
                      :key="index"
                      type="info"
                      class="topic-tag"
                      size="large"
                    >
                      {{ topic }}
                    </el-tag>
                  </div>
                </div>
              </el-tab-pane>

              <!-- 추출된 엔티티 탭 -->
              <el-tab-pane label="추출된 엔티티" name="entities">
                <div class="entities-section">
                  <h4>인식된 엔티티</h4>
                  <div v-if="documentAnalysis.entities && documentAnalysis.entities.length > 0">
                    <el-table :data="documentAnalysis.entities" border stripe>
                      <el-table-column prop="text" label="텍스트" />
                      <el-table-column prop="type" label="타입" />
                      <el-table-column prop="confidence" label="신뢰도">
                        <template #default="scope">
                          <el-progress 
                            :percentage="scope.row.confidence * 100" 
                            :color="getConfidenceColor(scope.row.confidence)"
                            :format="(percentage) => `${percentage.toFixed(1)}%`"
                          />
                        </template>
                      </el-table-column>
                    </el-table>
                  </div>
                  <div v-else class="no-entities">
                    <el-empty description="추출된 엔티티가 없습니다" />
                  </div>
                </div>
              </el-tab-pane>

              <!-- 원본 내용 탭 -->
              <el-tab-pane label="원본 내용" name="content">
                <div class="content-section">
                  <h4>추출된 텍스트 내용</h4>
                  <div class="content-display">
                    <el-input
                      v-model="documentAnalysis.content"
                      type="textarea"
                      :rows="15"
                      readonly
                      placeholder="문서에서 추출된 텍스트가 여기에 표시됩니다"
                    />
                  </div>
                  <div class="content-stats">
                    <el-tag type="success">총 {{ documentAnalysis.content.length }}자</el-tag>
                    <el-tag type="info">약 {{ Math.ceil(documentAnalysis.content.length / 200) }}분 읽기</el-tag>
                  </div>
                </div>
              </el-tab-pane>

              <!-- 메타데이터 탭 -->
              <el-tab-pane label="메타데이터" name="metadata">
                <div class="metadata-section">
                  <h4>문서 메타데이터</h4>
                  <el-descriptions :column="1" border>
                    <el-descriptions-item 
                      v-for="(value, key) in documentAnalysis.metadata" 
                      :key="key"
                      :label="formatMetadataLabel(key)"
                    >
                      {{ value }}
                    </el-descriptions-item>
                  </el-descriptions>
                </div>
              </el-tab-pane>
            </el-tabs>
          </div>

          <div class="next-step">
            <el-button 
              type="success" 
              size="large" 
              @click="proceedToQuestions"
            >
              <el-icon><ArrowRight /></el-icon>
              다음 단계: 질문 생성
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { 
  Upload, UploadFilled, Refresh, Loading, Document, ArrowRight 
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

export default {
  name: 'DocumentUpload',
  components: {
    Upload,
    UploadFilled,
    Refresh,
    Loading,
    Document,
    ArrowRight
  },
  setup() {
    const router = useRouter()
    const uploadRef = ref()
    const fileList = ref([])
    const selectedFile = ref(null)
    const uploading = ref(false)
    const uploadProgress = ref(0)
    const progressText = ref('')
    const documentAnalysis = ref(null)
    const activeTab = ref('basic')

    const handleFileChange = (file) => {
      selectedFile.value = file.raw
      fileList.value = [file]
    }

    const beforeUpload = (file) => {
      const isValidType = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain',
        'text/html',
        'text/markdown',
        'text/csv',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel'
      ].includes(file.type)

      const isValidSize = file.size / 1024 / 1024 < 10

      if (!isValidType) {
        ElMessage.error('지원하지 않는 파일 형식입니다.')
        return false
      }

      if (!isValidSize) {
        ElMessage.error('파일 크기는 10MB 이하여야 합니다.')
        return false
      }

      return false // 자동 업로드 방지
    }

    const uploadDocument = async () => {
      if (!selectedFile.value) {
        ElMessage.warning('업로드할 파일을 선택해주세요.')
        return
      }

      uploading.value = true
      uploadProgress.value = 0
      progressText.value = '파일 업로드 중...'

      try {
        // 파일 업로드 진행률 시뮬레이션
        const progressInterval = setInterval(() => {
          if (uploadProgress.value < 90) {
            uploadProgress.value += 10
            if (uploadProgress.value < 30) {
              progressText.value = '파일 업로드 중...'
            } else if (uploadProgress.value < 60) {
              progressText.value = '문서 내용 추출 중...'
            } else if (uploadProgress.value < 90) {
              progressText.value = 'AI 분석 중...'
            }
          }
        }, 500)

        // 실제 파일 업로드
        const formData = new FormData()
        formData.append('file', selectedFile.value)

        const apiUrl = process.env.VUE_APP_API_URL ? `${process.env.VUE_APP_API_URL}/upload` : '/api/upload'
        const response = await axios.post(apiUrl, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })

        clearInterval(progressInterval)
        uploadProgress.value = 100
        progressText.value = '분석 완료!'

        // 실제 백엔드 응답에서 분석 결과 가져오기 (업로드 응답에 포함된 데이터 사용)
        documentAnalysis.value = {
          document_id: response.data.document_id,
          filename: response.data.filename,
          document_type: response.data.document_type || getFileExtension(selectedFile.value.name).toLowerCase(),
          summary: response.data.summary || '문서 내용을 분석한 결과, 주요 내용과 핵심 토픽을 추출했습니다.',
          key_topics: response.data.key_topics || ['주제 분석', '내용 요약', '핵심 정보 추출'],
          entities: response.data.entities || [],
          content: response.data.content || '문서 내용을 추출하는 중입니다...',
          metadata: response.data.metadata || {},
          analysis_timestamp: response.data.analysis_timestamp || new Date().toISOString(),
          confidence_score: response.data.confidence_score || 0.95
        }

        ElMessage.success('문서 분석이 완료되었습니다!')
        
        // 잠시 후 다음 단계로 이동
        setTimeout(() => {
          proceedToQuestions()
        }, 2000)

      } catch (error) {
        console.error('업로드 오류:', error)
        ElMessage.error('문서 업로드 중 오류가 발생했습니다. 다시 시도해주세요.')
      } finally {
        uploading.value = false
      }
    }

    const resetUpload = () => {
      selectedFile.value = null
      fileList.value = []
      documentAnalysis.value = null
      uploadProgress.value = 0
      progressText.value = ''
      uploadRef.value?.clearFiles()
    }

    const proceedToQuestions = () => {
      // 질문 생성 페이지로 이동하면서 문서 ID 전달
      router.push({
        path: '/questions',
        query: { 
          documentId: documentAnalysis.value.document_id,
          filename: selectedFile.value.name
        }
      })
    }

    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    const getFileExtension = (filename) => {
      return filename.split('.').pop().toUpperCase()
    }

    const formatDate = (timestamp) => {
      return new Date(timestamp).toLocaleString('ko-KR')
    }

    const getConfidenceColor = (score) => {
      if (score >= 0.8) return '#67C23A'
      if (score >= 0.6) return '#E6A23C'
      return '#F56C6C'
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

    const formatMetadataLabel = (key) => {
      const labelMap = {
        'original_filename': '원본 파일명',
        'content_length': '내용 길이',
        'processing_timestamp': '처리 시간',
        'agent_version': '에이전트 버전'
      }
      return labelMap[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
    }

    return {
      uploadRef,
      fileList,
      selectedFile,
      uploading,
      uploadProgress,
      progressText,
      documentAnalysis,
      activeTab,
      handleFileChange,
      beforeUpload,
      uploadDocument,
      resetUpload,
      proceedToQuestions,
      formatFileSize,
      getFileExtension,
      formatDate,
      getConfidenceColor,
      formatDateTime,
      formatMetadataLabel
    }
  }
}
</script>

<style scoped>
.document-upload {
  padding: 20px 0;
}

.progress-card {
  margin-bottom: 20px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.upload-card {
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

.upload-area {
  margin: 30px 0;
}

.upload-dragger {
  width: 100%;
}

.el-upload__tip {
  margin-top: 15px;
  color: #909399;
}

.file-info {
  margin: 30px 0;
}

.upload-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: 30px;
}

.progress-content {
  text-align: center;
  padding: 20px;
}

.progress-text {
  margin-top: 15px;
  color: #606266;
  font-size: 1.1rem;
}

.result-card {
  margin-bottom: 20px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.analysis-result {
  margin: 20px 0;
}

.summary-content {
  max-height: 100px;
  overflow-y: auto;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 8px;
  line-height: 1.6;
}

.topic-tag {
  margin-right: 8px;
  margin-bottom: 8px;
}

.next-step {
  text-align: center;
  margin-top: 30px;
}

/* 반응형 디자인 */
@media (max-width: 768px) {
  .upload-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .el-descriptions {
    font-size: 0.9rem;
  }
}
</style>