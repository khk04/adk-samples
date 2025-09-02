<template>
  <div class="document-upload">
    <el-card class="upload-card">
      <template #header>
        <div class="card-header">
          <span>문서 업로드</span>
          <el-button @click="$router.push('/')" type="text" size="small">
            <el-icon><Back /></el-icon>
            홈으로 돌아가기
          </el-button>
        </div>
      </template>

      <!-- 업로드 영역 -->
      <div class="upload-area">
        <el-upload
          ref="uploadRef"
          class="upload-dragger"
          drag
          :action="uploadUrl"
          :headers="uploadHeaders"
          :data="uploadData"
          :before-upload="beforeUpload"
          :on-success="onUploadSuccess"
          :on-error="onUploadError"
          :on-progress="onUploadProgress"
          :file-list="fileList"
          :auto-upload="false"
          :multiple="false"
          accept=".pdf,.docx,.xlsx,.csv,.txt,.html"
        >
          <el-icon class="el-icon--upload" size="60" color="#409EFF">
            <UploadFilled />
          </el-icon>
          <div class="el-upload__text">
            <em>클릭하여 파일을 선택하거나</em>
            <br>
            <em>파일을 여기로 드래그하세요</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              지원 형식: PDF, DOCX, Excel, CSV, TXT, HTML (최대 50MB)
            </div>
          </template>
        </el-upload>
      </div>

      <!-- 업로드 버튼 -->
      <div class="upload-actions">
        <el-button 
          type="primary" 
          size="large" 
          @click="submitUpload"
          :loading="uploading"
          :disabled="fileList.length === 0"
        >
          <el-icon><Upload /></el-icon>
          {{ uploading ? '업로드 중...' : '문서 업로드' }}
        </el-button>
        <el-button 
          @click="clearFiles" 
          size="large"
          :disabled="fileList.length === 0"
        >
          <el-icon><Delete /></el-icon>
          파일 지우기
        </el-button>
      </div>

      <!-- 업로드 진행률 -->
      <el-progress 
        v-if="uploading" 
        :percentage="uploadProgress" 
        :status="uploadStatus"
        class="upload-progress"
      />

      <!-- 업로드된 문서 목록 -->
      <div v-if="uploadedDocuments.length > 0" class="uploaded-documents">
        <h3>업로드된 문서</h3>
        <el-table :data="uploadedDocuments" style="width: 100%">
          <el-table-column prop="filename" label="파일명" />
          <el-table-column prop="document_id" label="문서 ID" width="200" />
          <el-table-column prop="upload_time" label="업로드 시간" width="180" />
          <el-table-column label="작업" width="150">
            <template #default="scope">
              <el-button 
                @click="generateQuestions(scope.row)" 
                type="primary" 
                size="small"
              >
                질문 생성
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script>
import { 
  UploadFilled, 
  Upload, 
  Delete, 
  Back 
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

export default {
  name: 'DocumentUpload',
  components: {
    UploadFilled,
    Upload,
    Delete,
    Back
  },
  data() {
    return {
      uploadUrl: 'http://localhost:8000/upload',
      uploadHeaders: {},
      uploadData: {},
      fileList: [],
      uploading: false,
      uploadProgress: 0,
      uploadStatus: '',
      uploadedDocuments: []
    }
  },
  methods: {
    beforeUpload(file) {
      // 파일 크기 체크 (50MB)
      const isLt50M = file.size / 1024 / 1024 < 50
      if (!isLt50M) {
        ElMessage.error('파일 크기는 50MB를 초과할 수 없습니다!')
        return false
      }

      // 지원 형식 체크
      const supportedTypes = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/csv',
        'text/plain',
        'text/html'
      ]
      
      if (!supportedTypes.includes(file.type)) {
        ElMessage.error('지원하지 않는 파일 형식입니다!')
        return false
      }

      return true
    },

    async submitUpload() {
      if (this.fileList.length === 0) {
        ElMessage.warning('업로드할 파일을 선택해주세요.')
        return
      }

      this.uploading = true
      this.uploadProgress = 0
      this.uploadStatus = ''

      try {
        // 파일 업로드
        const formData = new FormData()
        formData.append('file', this.fileList[0].raw)

        const response = await axios.post(this.uploadUrl, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: (progressEvent) => {
            this.uploadProgress = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            )
          }
        })

        if (response.data) {
          const document = {
            filename: this.fileList[0].name,
            document_id: response.data.document_id,
            upload_time: new Date().toLocaleString('ko-KR')
          }

          this.uploadedDocuments.push(document)
          this.uploadStatus = 'success'
          
          ElMessage.success('문서가 성공적으로 업로드되었습니다!')
          
          // 파일 목록 초기화
          this.fileList = []
          this.uploadProgress = 0
        }
      } catch (error) {
        console.error('업로드 실패:', error)
        this.uploadStatus = 'exception'
        ElMessage.error('문서 업로드에 실패했습니다. 다시 시도해주세요.')
      } finally {
        this.uploading = false
      }
    },

    onUploadSuccess(response) {
      console.log('업로드 성공:', response)
    },

    onUploadError(error) {
      console.error('업로드 오류:', error)
      ElMessage.error('업로드 중 오류가 발생했습니다.')
    },

    onUploadProgress(event) {
      this.uploadProgress = Math.round((event.loaded * 100) / event.total)
    },

    clearFiles() {
      this.fileList = []
      this.uploadProgress = 0
      this.uploadStatus = ''
    },

    generateQuestions(document) {
      // 질문 생성 페이지로 이동하면서 문서 ID 전달
      this.$router.push({
        path: '/questions',
        query: { document_id: document.document_id }
      })
    }
  }
}
</script>

<style scoped>
.document-upload {
  max-width: 800px;
  margin: 0 auto;
}

.upload-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.upload-area {
  margin-bottom: 30px;
}

.upload-dragger {
  width: 100%;
}

.el-upload__text {
  margin: 20px 0;
  font-size: 16px;
  color: #606266;
}

.el-upload__tip {
  color: #909399;
  font-size: 14px;
}

.upload-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-bottom: 20px;
}

.upload-progress {
  margin-bottom: 20px;
}

.uploaded-documents {
  margin-top: 30px;
}

.uploaded-documents h3 {
  margin-bottom: 20px;
  color: #2c3e50;
  border-bottom: 2px solid #409EFF;
  padding-bottom: 10px;
}

@media (max-width: 768px) {
  .upload-actions {
    flex-direction: column;
  }
  
  .upload-actions .el-button {
    width: 100%;
  }
}
</style>