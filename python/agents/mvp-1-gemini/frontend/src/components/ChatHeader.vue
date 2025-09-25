<template>
  <header class="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between shadow-sm">
    <!-- 왼쪽: 사이드바 토글 및 제목 -->
    <div class="flex items-center space-x-3">
      <button 
        @click="toggleSidebar"
        class="p-2 rounded-lg hover:bg-gray-100 transition-colors"
        title="사이드바 토글"
        data-testid="sidebar-toggle"
      >
        <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
      
      <div class="flex items-center space-x-2">
        <div class="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
          <svg class="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clip-rule="evenodd" />
          </svg>
        </div>
        <div>
          <h1 class="text-lg font-semibold text-gray-900">MVP-1 Gemini</h1>
          <p class="text-sm text-gray-500">데이터 분석 및 리포트 생성 에이전트</p>
        </div>
      </div>
    </div>
    
    <!-- 오른쪽: 액션 버튼들 -->
    <div class="flex items-center space-x-2">
      <!-- 새 대화 버튼 -->
      <button 
        @click="startNewChat"
        class="px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors flex items-center space-x-1"
        title="새 대화 시작"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        <span>새 대화</span>
      </button>
      
      <!-- 설정 버튼 -->
      <button 
        @click="openSettings"
        class="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
        title="설정"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      </button>
      
      <!-- 사용자 프로필 -->
      <div class="flex items-center space-x-2 pl-2 border-l border-gray-200">
        <div class="w-8 h-8 bg-gradient-to-r from-green-400 to-blue-500 rounded-full flex items-center justify-center">
          <span class="text-white text-sm font-medium">U</span>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
// 이벤트 정의
const emit = defineEmits(['toggle-sidebar', 'new-chat', 'open-settings'])

// 메서드
const toggleSidebar = () => {
  emit('toggle-sidebar')
}

const startNewChat = () => {
  emit('new-chat')
}

const openSettings = () => {
  emit('open-settings')
}
</script>

 