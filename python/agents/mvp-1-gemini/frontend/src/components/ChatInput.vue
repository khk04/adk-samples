<template>
  <div class="border-t border-gray-200 bg-white">
    <!-- 입력 컨테이너 -->
    <div class="w-full px-4 py-4">
      <div class="relative">
        <!-- 텍스트 입력 영역 -->
        <div class="relative">
          <textarea
            :value="modelValue"
            @input="handleInput"
            @keydown="handleKeydown"
            placeholder="데이터 확인이나 리포트 생성을 요청하세요... 예: '데이터 확인해줘' 또는 '리포트를 만들어줘'"
            class="w-full px-4 py-3 pr-12 border border-gray-300 rounded-xl resize-none font-inherit text-sm leading-relaxed outline-none transition-all duration-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 focus:ring-opacity-50 bg-white shadow-sm text-black"
            :class="{
              'opacity-75': loading,
              'pr-16': modelValue.trim() && !loading
            }"
            rows="1"
            ref="textareaRef"
            :disabled="loading"
            data-testid="chat-input"
          ></textarea>
          
          <!-- 문자 수 표시 -->
          <div v-if="modelValue.trim() && !loading" class="absolute bottom-3 right-3 text-xs text-gray-400">
            {{ modelValue.length }}/4000
          </div>
        </div>
        
        <!-- 전송 버튼 -->
        <button 
          @click="handleSend"
          :disabled="!canSend || loading"
          class="absolute bottom-2 right-2 p-2 bg-blue-600 text-white border-none rounded-lg cursor-pointer transition-all duration-200 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed shadow-sm hover:shadow-md disabled:shadow-none"
          :class="{
            'animate-pulse': loading
          }"
          data-testid="chat-input-send"
        >
          <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button>
      </div>
      
      <!-- 도움말 텍스트 -->
      <div class="mt-2 text-xs text-gray-500 text-center">
        <kbd class="px-2 py-1 bg-gray-100 rounded text-gray-600">Enter</kbd> 전송 • 
        <kbd class="px-2 py-1 bg-gray-100 rounded text-gray-600">Shift + Enter</kbd> 줄바꿈
      </div>
      
      <!-- 추가 기능 버튼들 -->
      <div class="flex items-center justify-center space-x-4 mt-3">
        <button 
          @click="attachFile"
          class="flex items-center space-x-1 text-xs text-gray-500 hover:text-gray-700 transition-colors"
          title="파일 첨부"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
          </svg>
          <span>파일 첨부</span>
        </button>
        
        <button 
          @click="clearChat"
          class="flex items-center space-x-1 text-xs text-gray-500 hover:text-gray-700 transition-colors"
          title="대화 지우기"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          <span>대화 지우기</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch } from 'vue'

// Props & Emits
const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'send', 'typing', 'attach-file', 'clear-chat'])

// Refs
const textareaRef = ref(null)

// 계산된 속성
const canSend = computed(() => {
  return props.modelValue.trim() && !props.loading && props.modelValue.length <= 4000
})

// 메서드
const handleInput = (event) => {
  const value = event.target.value
  emit('update:modelValue', value)
  emit('typing', value)
  
  // 자동 높이 조정
  nextTick(() => {
    adjustTextareaHeight()
  })
}

const handleKeydown = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    handleSend()
  }
}

const handleSend = () => {
  if (canSend.value) {
    emit('send')
  }
}

const adjustTextareaHeight = () => {
  const textarea = textareaRef.value
  if (textarea) {
    textarea.style.height = 'auto'
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px'
  }
}

const attachFile = () => {
  emit('attach-file')
}

const clearChat = () => {
  emit('clear-chat')
}

// 포커스 설정 메서드
const focus = () => {
  if (textareaRef.value) {
    textareaRef.value.focus()
  }
}

// 외부에서 포커스 메서드에 접근할 수 있도록 expose
defineExpose({
  focus
})

// 감시자
watch(() => props.modelValue, () => {
  nextTick(() => {
    adjustTextareaHeight()
  })
})

// 컴포넌트 마운트 시 초기 높이 조정 및 포커스
nextTick(() => {
  adjustTextareaHeight()
  focus()
})
</script>

 