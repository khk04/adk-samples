<template>
  <div 
    :class="[
      'group relative w-full',
      message.type === 'user' ? 'bg-white' : 'bg-gray-50'
    ]"
    :data-testid="message.type === 'user' ? 'chat-message-user' : (message.type === 'bot' ? 'chat-message-bot' : null)"
  >
    <!-- 메시지 컨테이너 -->
    <div class="w-full px-4 py-6">
      <div class="flex space-x-4">
        <!-- 아바타 -->
        <div class="flex-shrink-0">
          <div 
            :class="[
              'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium',
              message.type === 'user' 
                ? 'bg-gradient-to-r from-green-400 to-blue-500 text-white' 
                : 'bg-gradient-to-r from-blue-500 to-purple-600 text-white'
            ]"
          >
            <span v-if="message.type === 'user'">U</span>
            <svg v-else class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clip-rule="evenodd" />
            </svg>
          </div>
        </div>
        
        <!-- 메시지 내용 -->
        <div class="flex-1 min-w-0">
          <!-- 메시지 헤더 -->
          <div class="flex items-center space-x-2 mb-2">
            <span class="text-sm font-medium text-gray-900">
              {{ message.type === 'user' ? '사용자' : 'LLM File Search' }}
            </span>
            <span class="text-xs text-gray-500">{{ formatTime(message.timestamp) }}</span>
            
            <!-- 메시지 상태 -->
            <div v-if="message.type === 'user'" class="flex items-center">
              <MessageStatus :status="message.status" />
            </div>
          </div>
          
          <!-- 메시지 텍스트 -->
          <div class="max-w-none">
            <div class="text-gray-900 leading-relaxed whitespace-pre-wrap">
              {{ message.text }}
            </div>
          </div>
          
          <!-- 검색 결과 표시 (봇 메시지인 경우) -->
          <SearchResults 
            v-if="message.type === 'bot' && searchResults && searchResults.length > 0"
            :search-results="searchResults"
          />
          
          <!-- 메시지 액션 버튼들 (호버 시 표시) -->
          <div class="flex items-center space-x-2 mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
            <button 
              @click="copyMessage"
              class="p-1 text-gray-400 hover:text-gray-600 rounded transition-colors"
              title="메시지 복사"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </button>
            
            <button 
              @click="regenerateMessage"
              v-if="message.type === 'bot'"
              class="p-1 text-gray-400 hover:text-gray-600 rounded transition-colors"
              title="다시 생성"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
            
            <button 
              @click="likeMessage"
              class="p-1 text-gray-400 hover:text-gray-600 rounded transition-colors"
              :class="{ 'text-green-500': message.liked }"
              title="좋아요"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
              </svg>
            </button>
            
            <button 
              @click="dislikeMessage"
              class="p-1 text-gray-400 hover:text-gray-600 rounded transition-colors"
              :class="{ 'text-red-500': message.disliked }"
              title="싫어요"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018c.163 0 .326.02.485.06L17 4m-7 10v5a2 2 0 002 2h.095c.5 0 .905-.405.905-.905 0-.714.211-1.412.608-2.006L17 13V4m-7 10h2" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import MessageStatus from './MessageStatus.vue'
import SearchResults from './SearchResults.vue'

// Props 정의
const props = defineProps({
  message: {
    type: Object,
    required: true
  },
  isLast: {
    type: Boolean,
    default: false
  },
  searchResults: {
    type: Array,
    default: () => []
  }
})

// Emits 정의
const emit = defineEmits(['copy', 'regenerate', 'like', 'dislike'])

// 계산된 속성
const messageClasses = computed(() => {
  const baseClasses = 'transition-all duration-200'
  
  if (props.message.type === 'user') {
    return `${baseClasses} bg-blue-600 text-white rounded-br-sm ${
      props.message.status === 'sending' ? 'opacity-75' : ''
    }`
  } else {
    return `${baseClasses} bg-white text-gray-800 border border-gray-200 rounded-bl-sm hover:shadow-md`
  }
})

// 시간 포맷팅
const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString('ko-KR', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 메서드
const copyMessage = () => {
  navigator.clipboard.writeText(props.message.text)
  emit('copy', props.message)
}

const regenerateMessage = () => {
  emit('regenerate', props.message)
}

const likeMessage = () => {
  emit('like', props.message)
}

const dislikeMessage = () => {
  emit('dislike', props.message)
}
</script>

 