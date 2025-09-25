<template>
  <div class="flex flex-col h-screen w-full h-full bg-gray-50">
    <!-- 헤더 -->
    <ChatHeader 
      @toggle-sidebar="toggleSidebar"
      @new-chat="startNewChat"
      @open-settings="openSettings"
    />
    
    <!-- 메인 콘텐츠 영역 -->
    <div class="flex flex-1 overflow-hidden">
      <!-- 사이드바 -->
      <ChatSidebar 
        v-if="sidebarOpen"
        :is-open="sidebarOpen"
        :chat-history="chatHistory"
        class="fixed left-0 top-0 h-full z-50 w-80 transition-all duration-300 overflow-hidden"
        @close="closeSidebar"
        @new-chat="startNewChat"
        @select-chat="selectChat"
        @delete-chat="deleteChat"
        @clear-all="clearAllChats"
        @export="exportChats"
        @settings="openSettings"
      />
      
      <!-- 메시지 영역 -->
      <div ref="messageAreaRef" class="flex-1 flex flex-col overflow-hidden min-w-0">
        <div 
          class="flex-1 overflow-y-auto scroll-smooth" 
          ref="messagesContainer"
        >
          <TransitionGroup name="message" tag="div" class="w-full">
            <ChatMessage 
              v-for="(message, index) in messages" 
              :key="`${message.id}-${index}`"
              :message="message"
              :is-last="index === messages.length - 1"
              :search-results="getSearchResultsForMessage(message)"
              @copy="handleCopyMessage"
              @regenerate="handleRegenerateMessage"
              @like="handleLikeMessage"
              @dislike="handleDislikeMessage"
            />
          </TransitionGroup>
          
          <!-- 로딩 인디케이터 -->
          <div v-if="isLoading" class="group relative bg-gray-50">
            <div class="w-full px-4 py-6">
              <div class="flex space-x-4">
                <div class="flex-shrink-0">
                  <div class="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                    <svg class="w-4 h-4 text-white animate-pulse" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clip-rule="evenodd" />
                    </svg>
                  </div>
                </div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center space-x-2 mb-2">
                    <span class="text-sm font-medium text-gray-900">MVP-1 Gemini</span>
                    <span class="text-xs text-gray-500">분석 중...</span>
                  </div>
                  <div class="flex space-x-1">
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 입력 영역 -->
        <ChatInput 
          ref="chatInputRef"
          v-model="newMessage"
          :loading="isLoading"
          @send="sendMessage"
          @typing="handleTyping"
          @attach-file="handleAttachFile"
          @clear-chat="handleClearChat"
        />
      </div>
    </div>
    
    <!-- 모바일 오버레이 -->
    <div 
      v-if="sidebarOpen"
      @click="closeSidebar"
      class="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
    ></div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, watch, computed } from 'vue'
import { chatAPI } from '../services/api'
import ChatHeader from './ChatHeader.vue'
import ChatMessage from './ChatMessage.vue'
import ChatInput from './ChatInput.vue'
import ChatSidebar from './ChatSidebar.vue'

// 상태 관리
const messages = ref([])
const currentChatId = ref(null)
const newMessage = ref('')
const messagesContainer = ref(null)
const messageAreaRef = ref(null)
const chatInputRef = ref(null)
const isLoading = ref(false)
const isTyping = ref(false)
const sidebarOpen = ref(false)
const windowWidth = ref(window.innerWidth)
const messageAreaWidth = ref(0)
const messageSearchResults = ref({})  // 메시지별 검색 결과 저장
const chatHistory = ref([]) // 최근 대화 리스트

// 계산된 속성
const canSendMessage = computed(() => {
  return newMessage.value.trim() && !isLoading.value
})

// 메시지별 검색 결과 반환
const getSearchResultsForMessage = (message) => {
  return messageSearchResults.value[message.id] || []
}

// 초기 채팅 로드
const loadInitialChat = async () => {
  try {
    const response = await chatAPI.getChats()
    if (response.data && response.data.length > 0) {
      // chatHistory 갱신
      chatHistory.value = response.data.map(chat => {
        const lastMsg = (chat.messages && chat.messages.length > 0) ? chat.messages[chat.messages.length - 1] : null
        return {
          id: chat.id,
          title: lastMsg ? lastMsg.text.slice(0, 20) : '새로운 대화',
          lastMessageTime: lastMsg ? new Date(lastMsg.timestamp) : new Date(),
          messageCount: chat.messages ? chat.messages.length : 0
        }
      })
      const firstChat = response.data[0]
      currentChatId.value = firstChat.id
      messages.value = firstChat.messages || []
    } else {
      chatHistory.value = []
      await startNewChat()
    }
  } catch (error) {
    console.error('초기 채팅 로드 실패:', error)
    chatHistory.value = []
    // 오류 시 기본 메시지 표시
    messages.value = [{
      id: Date.now(),
      text: '안녕하세요! MVP-1 Gemini 데이터 분석 에이전트에 오신 것을 환영합니다. 데이터 확인이나 리포트 생성을 요청하시면 언제든 말씀해 주세요.',
      type: 'bot',
      timestamp: new Date(),
      status: 'sent',
      liked: false,
      disliked: false
    }]
  }
}

// 메시지 전송
const sendMessage = async () => {
  if (!canSendMessage.value) return
  
  const userMessage = {
    id: Date.now(),
    text: newMessage.value.trim(),
    type: 'user',
    timestamp: new Date(),
    status: 'sending',
    liked: false,
    disliked: false
  }
  
  messages.value.push(userMessage)
  const messageText = newMessage.value.trim()
  newMessage.value = ''
  isLoading.value = true
  
  // 입력창 포커스 및 스크롤
  await nextTick()
  scrollToBottom()
  
  try {
    // 백엔드 API 호출
    const response = await chatAPI.sendMessage(currentChatId.value, messageText)
    
    // 사용자 메시지 상태 업데이트
    userMessage.status = 'sent'
    
    // 봇 응답 추가
    if (response.data && response.data.message) {
      const botMessage = {
        ...response.data.message,
        timestamp: new Date(response.data.message.timestamp)
      }
      messages.value.push(botMessage)
      
      // 검색 결과 저장
      if (response.data.search_results) {
        messageSearchResults.value[botMessage.id] = response.data.search_results
      }
    }
    
    // 채팅 ID 업데이트 (새 채팅인 경우)
    if (response.data && response.data.chat_id) {
      currentChatId.value = response.data.chat_id
    }
    
  } catch (error) {
    console.error('메시지 전송 실패:', error)
    userMessage.status = 'error'
    
    // 오류 메시지 추가
    const errorMessage = {
      id: Date.now(),
      text: '메시지 전송 중 오류가 발생했습니다. 다시 시도해 주세요.',
      type: 'bot',
      timestamp: new Date(),
      status: 'error',
      liked: false,
      disliked: false
    }
    messages.value.push(errorMessage)
  } finally {
    isLoading.value = false
    
    // 메시지 전송 후 입력창에 포커스 다시 설정
    await nextTick()
    scrollToBottom()
    if (chatInputRef.value) {
      chatInputRef.value.focus()
    }
  }
}

// 스크롤 최적화
const scrollToBottom = () => {
  if (messagesContainer.value) {
    const container = messagesContainer.value
    container.scrollTop = container.scrollHeight
  }
}

// 메시지 영역 너비 측정
const measureMessageAreaWidth = () => {
  if (messageAreaRef.value) {
    messageAreaWidth.value = messageAreaRef.value.offsetWidth
  }
}

// 사이드바 관련 메서드
const toggleSidebar = async () => {
  sidebarOpen.value = !sidebarOpen.value
  if (sidebarOpen.value) {
    // 사이드바가 열릴 때마다 최신 chat 리스트를 백엔드에서 가져옴
    try {
      const response = await chatAPI.getChats()
      chatHistory.value = response.data.map(chat => {
        const lastMsg = (chat.messages && chat.messages.length > 0) ? chat.messages[chat.messages.length - 1] : null
        return {
          id: chat.id,
          title: lastMsg ? lastMsg.text.slice(0, 20) : '새로운 대화',
          lastMessageTime: lastMsg ? new Date(lastMsg.timestamp) : new Date(),
          messageCount: chat.messages ? chat.messages.length : 0
        }
      })
    } catch (error) {
      console.error('사이드바 채팅 목록 갱신 실패:', error)
    }
  }
  nextTick(() => {
    measureMessageAreaWidth()
  })
}

const closeSidebar = () => {
  sidebarOpen.value = false
  nextTick(() => {
    measureMessageAreaWidth()
  })
}

const selectChat = async (chat) => {
  try {
    const response = await chatAPI.getChat(chat.id)
    currentChatId.value = chat.id
    messages.value = response.data.messages || []
  } catch (error) {
    console.error('채팅 로드 실패:', error)
  }
}

const deleteChat = async (chatId) => {
  try {
    await chatAPI.deleteChat(chatId)
    if (currentChatId.value === chatId) {
      await startNewChat()
    }
  } catch (error) {
    console.error('채팅 삭제 실패:', error)
  }
}

const clearAllChats = async () => {
  if (confirm('모든 대화를 지우시겠습니까?')) {
    try {
      await chatAPI.clearAllChats()
      await startNewChat()
    } catch (error) {
      console.error('모든 채팅 삭제 실패:', error)
    }
  }
}

const exportChats = async () => {
  try {
    const response = await chatAPI.exportAllChats()
    const dataStr = JSON.stringify(response.data, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `chat-export-${new Date().toISOString().split('T')[0]}.json`
    link.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    console.error('채팅 내보내기 실패:', error)
  }
}

// 이벤트 핸들러들
const handleTyping = (value) => {
  // 타이핑 상태 관리 (필요시)
}

const handleCopyMessage = (message) => {
  navigator.clipboard.writeText(message.text).then(() => {
    console.log('메시지가 클립보드에 복사되었습니다:', message.text)
  }).catch(err => {
    console.error('복사 실패:', err)
  })
}

const handleRegenerateMessage = async (message) => {
  if (message.type === 'bot' && currentChatId.value) {
    try {
      const response = await chatAPI.regenerateMessage(currentChatId.value, message.id)
      
      // 해당 메시지 교체
      const index = messages.value.findIndex(m => m.id === message.id)
      if (index > -1 && response.data.new_message) {
        messages.value[index] = {
          ...response.data.new_message,
          timestamp: new Date(response.data.new_message.timestamp)
        }
      }
    } catch (error) {
      console.error('메시지 재생성 실패:', error)
    }
  }
}

const handleLikeMessage = async (message) => {
  if (currentChatId.value) {
    try {
      const response = await chatAPI.likeMessage(currentChatId.value, message.id)
      message.liked = response.data.liked
      if (message.liked) message.disliked = false
    } catch (error) {
      console.error('메시지 좋아요 실패:', error)
    }
  }
}

const handleDislikeMessage = async (message) => {
  if (currentChatId.value) {
    try {
      const response = await chatAPI.dislikeMessage(currentChatId.value, message.id)
      message.disliked = response.data.disliked
      if (message.disliked) message.liked = false
    } catch (error) {
      console.error('메시지 싫어요 실패:', error)
    }
  }
}

const startNewChat = async () => {
  try {
    // 백엔드에 새 채팅 생성 요청
    const response = await chatAPI.createChat()
    if (response.data && response.data.id) {
      currentChatId.value = response.data.id
    } else {
      currentChatId.value = 0
    }
    messages.value = []
    messageSearchResults.value = {}  // 검색 결과 초기화
    // 새 대화 시작 후 입력창에 포커스 설정
    nextTick(() => {
      if (chatInputRef.value) {
        chatInputRef.value.focus()
      }
    })
  } catch (error) {
    console.error('새 채팅 생성 실패:', error)
    // 오류 시 기본 메시지로 시작
    messages.value = [{
      id: Date.now(),
      text: '새로운 대화를 시작합니다. 데이터 확인이나 리포트 생성을 요청하시면 언제든 말씀해 주세요.',
      type: 'bot',
      timestamp: new Date(),
      status: 'sent',
      liked: false,
      disliked: false
    }]
    currentChatId.value = 0
  }
}

const openSettings = () => {
  // 설정 모달 열기 로직
  console.log('설정 열기')
}

const handleAttachFile = () => {
  // 파일 첨부 로직
  console.log('파일 첨부')
}

const handleClearChat = () => {
  if (confirm('모든 대화 내용을 지우시겠습니까?')) {
    startNewChat()
  }
}

// 메시지 변경 감지
watch(messages, () => {
  nextTick(() => scrollToBottom())
}, { deep: true })

// 컴포넌트 마운트
onMounted(async () => {
  // 초기 채팅 로드
  await loadInitialChat()
  
  // 초기 너비 측정
  nextTick(() => {
    measureMessageAreaWidth()
  })
  
  // 윈도우 리사이즈 이벤트
  window.addEventListener('resize', () => {
    windowWidth.value = window.innerWidth
    measureMessageAreaWidth()
  })
})
</script>

