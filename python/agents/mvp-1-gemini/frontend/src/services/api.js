import axios from 'axios'

// API 기본 설정
// MVP-1 Gemini 백엔드 서버 주소
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 90000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 요청 인터셉터
api.interceptors.request.use(
  (config) => {
    console.log('API 요청:', config.method?.toUpperCase(), config.url)
    return config
  },
  (error) => {
    console.error('API 요청 오류:', error)
    return Promise.reject(error)
  }
)

// 응답 인터셉터
api.interceptors.response.use(
  (response) => {
    console.log('API 응답:', response.status, response.config.url)
    return response
  },
  (error) => {
    console.error('API 응답 오류:', error.response?.status, error.response?.data)
    return Promise.reject(error)
  }
)

// MVP-1 Gemini 채팅 관련 API
export const chatAPI = {
  // 채팅 목록 조회 (ADK는 세션 기반이므로 단순화)
  getChats: () => Promise.resolve({ data: [] }),
  
  // 새 채팅 생성 (ADK는 세션 기반이므로 단순화)
  createChat: () => Promise.resolve({ data: { id: Date.now() } }),
  
  // 특정 채팅 조회 (ADK는 세션 기반이므로 단순화)
  getChat: (chatId) => Promise.resolve({ data: { messages: [] } }),
  
  // 채팅 삭제 (ADK는 세션 기반이므로 단순화)
  deleteChat: (chatId) => Promise.resolve({ data: { success: true } }),
  
  // 모든 채팅 삭제 (ADK는 세션 기반이므로 단순화)
  clearAllChats: () => Promise.resolve({ data: { success: true } }),
  
  // 메시지 전송 - MVP-1 Gemini의 핵심 API
  sendMessage: (chatId, message) => api.post('/chat', { 
    message: message,
    session_id: chatId || 'default'
  }),
  
  // 메시지 재생성 (ADK는 지원하지 않으므로 단순화)
  regenerateMessage: (chatId, messageId) => Promise.resolve({ data: { new_message: null } }),
  
  // 메시지 좋아요 (ADK는 지원하지 않으므로 단순화)
  likeMessage: (chatId, messageId) => Promise.resolve({ data: { liked: false } }),
  
  // 메시지 싫어요 (ADK는 지원하지 않으므로 단순화)
  dislikeMessage: (chatId, messageId) => Promise.resolve({ data: { disliked: false } }),
  
  // 채팅 내보내기 (ADK는 지원하지 않으므로 단순화)
  exportChat: (chatId) => Promise.resolve({ data: {} }),
  
  // 모든 채팅 내보내기 (ADK는 지원하지 않으므로 단순화)
  exportAllChats: () => Promise.resolve({ data: {} }),
}

// 파일 검색 관련 API
export const searchAPI = {
  // 파일 검색
  searchFiles: (query) => api.post('/api/search', null, { params: { query } }),
  
  // 파일 업로드
  uploadFile: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },
}

// 설정 관련 API
export const settingsAPI = {
  // 설정 조회
  getSettings: () => api.get('/api/settings'),
  
  // 설정 업데이트
  updateSettings: (settings) => api.put('/api/settings', settings),
}

// 헬스 체크
export const healthAPI = {
  checkHealth: () => api.get('/api/health'),
}

export default api 