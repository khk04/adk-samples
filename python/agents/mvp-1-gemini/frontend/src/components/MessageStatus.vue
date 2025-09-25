<template>
  <div class="flex items-center space-x-1">
    <!-- 전송 중 -->
    <div v-if="status === 'sending'" class="flex space-x-1">
      <div class="w-1 h-1 bg-white rounded-full animate-bounce"></div>
      <div class="w-1 h-1 bg-white rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
      <div class="w-1 h-1 bg-white rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
    </div>
    
    <!-- 전송 완료 -->
    <div v-else-if="status === 'sent'" class="text-green-300">
      <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
      </svg>
    </div>
    
    <!-- 전송 실패 -->
    <div v-else-if="status === 'error'" class="text-red-300">
      <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
      </svg>
    </div>
  </div>
</template>

<script setup>
defineProps({
  status: {
    type: String,
    required: true,
    validator: (value) => ['sending', 'sent', 'error'].includes(value)
  }
})
</script> 