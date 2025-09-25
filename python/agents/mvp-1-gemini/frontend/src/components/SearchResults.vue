<template>
  <div v-if="searchResults && searchResults.length > 0" class="mt-4">
    <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <div class="flex items-center mb-3">
        <svg class="w-5 h-5 text-blue-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
        </svg>
        <h3 class="text-sm font-medium text-blue-900">찾은 문서</h3>
        <span class="ml-2 text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded-full">
          {{ searchResults.length }}개
        </span>
      </div>
      
      <div class="space-y-3">
        <div 
          v-for="(result, index) in searchResults" 
          :key="index"
          class="bg-white border border-blue-200 rounded-md p-3 hover:shadow-sm transition-shadow"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1 min-w-0">
              <div class="flex items-center mb-2">
                <svg class="w-4 h-4 text-gray-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                </svg>
                <span class="text-sm font-medium text-gray-900 truncate">
                  {{ result.file_path }}
                </span>
                <span class="ml-2 text-xs text-gray-500">
                  (관련도: {{ Math.round(result.relevance_score * 100) }}%)
                </span>
              </div>
              
              <div class="text-sm text-gray-700 leading-relaxed">
                <p class="line-clamp-3">{{ result.content }}</p>
              </div>
              
              <div class="flex items-center mt-2 space-x-2">
                <button 
                  @click="copyContent(result.content)"
                  class="text-xs text-blue-600 hover:text-blue-800 flex items-center"
                >
                  <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                  </svg>
                  복사
                </button>
                
                <button 
                  @click="openFile(result.file_path)"
                  class="text-xs text-green-600 hover:text-green-800 flex items-center"
                >
                  <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                  </svg>
                  열기
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps } from 'vue'

const props = defineProps({
  searchResults: {
    type: Array,
    default: () => []
  }
})

const copyContent = async (content) => {
  try {
    await navigator.clipboard.writeText(content)
    // 실제로는 토스트 메시지 표시
    console.log('내용이 클립보드에 복사되었습니다.')
  } catch (err) {
    console.error('복사 실패:', err)
  }
}

const openFile = (filePath) => {
  // 실제로는 파일 열기 로직 구현
  console.log('파일 열기:', filePath)
  // 예: 새 탭에서 파일 열기 또는 다운로드
  window.open(`/api/files/${encodeURIComponent(filePath)}`, '_blank')
}
</script>

 