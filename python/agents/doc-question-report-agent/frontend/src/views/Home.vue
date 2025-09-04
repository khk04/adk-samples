<template>
  <div class="home">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card class="welcome-card">
          <template #header>
            <div class="clearfix">
              <span>시스템 개요</span>
            </div>
          </template>
          <div class="welcome-content">
            <h2>Document Question & Report Agent</h2>
            <p>이 시스템은 2-Agent 시스템으로 문서 분석과 리포트 생성을 수행합니다:</p>
            
            <el-row :gutter="20" style="margin-top: 20px;">
              <el-col :span="12">
                <el-card class="agent-card">
                  <template #header>
                    <div>
                      <i class="el-icon-document"></i>
                      Document & Question Agent
                    </div>
                  </template>
                  <ul>
                    <li>문서 분석 및 텍스트 추출</li>
                    <li>질문 후보 생성</li>
                    <li>컨텍스트 관리</li>
                    <li>정보 추출 및 요약</li>
                  </ul>
                </el-card>
              </el-col>
              
              <el-col :span="12">
                <el-card class="agent-card">
                  <template #header>
                    <div>
                      <i class="el-icon-edit-outline"></i>
                      Report Agent
                    </div>
                  </template>
                  <ul>
                    <li>리포트 초안 생성</li>
                    <li>데이터 시각화</li>
                    <li>포맷 변환</li>
                    <li>출력 최적화</li>
                  </ul>
                </el-card>
              </el-col>
            </el-row>
            
            <div class="action-buttons">
              <el-button type="primary" size="large" @click="goToUpload">
                <i class="el-icon-upload"></i>
                문서 업로드 시작
              </el-button>
              
              <el-button type="info" size="large" @click="checkStatus">
                <i class="el-icon-info"></i>
                시스템 상태 확인
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card v-if="systemStatus">
          <template #header>
            <div>
              <span>시스템 상태</span>
              <el-button style="float: right; padding: 3px 0" type="text" @click="checkStatus">
                <i class="el-icon-refresh"></i> 새로고침
              </el-button>
            </div>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="시스템 ID">{{ systemStatus.system_id }}</el-descriptions-item>
            <el-descriptions-item label="상태">{{ systemStatus.status }}</el-descriptions-item>
            <el-descriptions-item label="문서 수">{{ systemStatus.cache_stats.documents }}</el-descriptions-item>
            <el-descriptions-item label="질문 세트 수">{{ systemStatus.cache_stats.questions }}</el-descriptions-item>
            <el-descriptions-item label="리포트 수">{{ systemStatus.cache_stats.reports }}</el-descriptions-item>
            <el-descriptions-item label="활성 태스크">{{ systemStatus.cache_stats.active_tasks }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Home',
  data() {
    return {
      systemStatus: null
    }
  },
  mounted() {
    this.checkStatus()
  },
  methods: {
    goToUpload() {
      this.$router.push('/upload')
    },
    async checkStatus() {
      try {
        const response = await axios.get('/api/status')
        this.systemStatus = response.data
      } catch (error) {
        this.$message.error('시스템 상태를 가져올 수 없습니다.')
        console.error(error)
      }
    }
  }
}
</script>

<style scoped>
.welcome-card {
  margin-bottom: 20px;
}

.welcome-content h2 {
  color: #409EFF;
  margin-bottom: 15px;
}

.agent-card {
  height: 200px;
}

.agent-card ul {
  list-style: none;
  padding: 0;
}

.agent-card li {
  padding: 5px 0;
  border-bottom: 1px solid #f0f0f0;
}

.agent-card li:last-child {
  border-bottom: none;
}

.action-buttons {
  margin-top: 30px;
  text-align: center;
}

.action-buttons .el-button {
  margin: 0 10px;
}
</style>