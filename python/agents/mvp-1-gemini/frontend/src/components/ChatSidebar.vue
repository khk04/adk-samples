<template>
  <div 
    class="bg-white border-r border-gray-200 h-full flex flex-col relative z-50"
  >
    <!-- 사이드바 헤더 -->
    <div class="flex items-center justify-between p-4 border-b border-gray-200">
      <h2 class="text-lg font-semibold text-gray-900">대화</h2>
      <button 
        @click="closeSidebar"
        class="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
    
    <!-- 새 대화 버튼 -->
    <div class="p-4 border-b border-gray-200">
      <button 
        @click="startNewChat"
        class="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        data-testid="chat-sidebar-new-chat"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        <span>새 대화</span>
      </button>
    </div>
    
    <!-- 대화 히스토리 -->
    <div class="flex-1 overflow-y-auto">
      <div class="p-4">
        <h3 class="text-sm font-medium text-gray-700 mb-3">최근 대화</h3>
        
        <div v-if="chatHistory.length === 0" class="text-center py-8">
          <svg class="w-12 h-12 text-gray-300 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          <p class="text-sm text-gray-500">아직 대화가 없습니다</p>
        </div>
        
        <div v-else class="space-y-2">
          <div 
            v-for="chat in chatHistory" 
            :key="chat.id"
            data-testid="chat-sidebar-item"
            @click="selectChat(chat)"
            :class="[
              'p-3 rounded-lg cursor-pointer transition-colors',
              selectedChatId === chat.id ? 'bg-blue-50 border border-blue-200' : 'hover:bg-gray-50'
            ]"
          >
            <div class="flex items-start justify-between">
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-gray-900 truncate">
                  {{ chat.title }}
                </p>
                <p class="text-xs text-gray-500 mt-1">
                  {{ formatDate(chat.lastMessageTime) }}
                </p>
              </div>
              <button 
                @click.stop="deleteChat(chat.id)"
                class="p-1 text-gray-400 hover:text-red-500 rounded transition-colors opacity-0 group-hover:opacity-100"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 사이드바 푸터 -->
    <div class="p-4 border-t border-gray-200">
      <div class="space-y-2">
        <button 
          @click="openSettings"
          class="w-full flex items-center space-x-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <span>설정</span>
        </button>
        
        <button 
          @click="exportChats"
          class="w-full flex items-center space-x-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span>대화 내보내기</span>
        </button>
        
        <button 
          @click="clearAllChats"
          class="w-full flex items-center space-x-2 px-3 py-2 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          <span>모든 대화 지우기</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

// Props
const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  chatHistory: {
    type: Array,
    default: () => []
  }
})

// Emits
const emit = defineEmits(['close', 'new-chat', 'select-chat', 'delete-chat', 'clear-all', 'export', 'settings'])

// 상태
const selectedChatId = ref(null)

// 메서드
const closeSidebar = () => {
  emit('close')
}

const startNewChat = () => {
  emit('new-chat')
  closeSidebar()
}

const selectChat = (chat) => {
  selectedChatId.value = chat.id
  emit('select-chat', chat)
  closeSidebar()
}

const deleteChat = (chatId) => {
  if (confirm('이 대화를 삭제하시겠습니까?')) {
    emit('delete-chat', chatId)
  }
}

const clearAllChats = () => {
  if (confirm('모든 대화를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) {
    emit('clear-all')
  }
}

const exportChats = () => {
  emit('export')
}

const openSettings = () => {
  emit('settings')
  closeSidebar()
}

// 날짜 포맷팅
const formatDate = (date) => {
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (minutes < 60) {
    return `${minutes}분 전`
  } else if (hours < 24) {
    return `${hours}시간 전`
  } else if (days < 7) {
    return `${days}일 전`
  } else {
    return date.toLocaleDateString('ko-KR')
  }
}
</script>

 