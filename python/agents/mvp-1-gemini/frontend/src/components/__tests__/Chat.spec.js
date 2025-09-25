// @vitest-environment jsdom
import { describe, it, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import Chat from '../Chat.vue'

// chatAPI 모킹 (getChats, getChat, sendMessage 모두 포함)
vi.mock('../../services/api', () => ({
  chatAPI: {
    getChats: vi.fn().mockResolvedValue({
      data: [
        { id: 'chat1', title: '테스트 채팅', messages: [] }
      ]
    }),
    getChat: vi.fn().mockResolvedValue({
      data: { id: 'chat1', title: '테스트 채팅', messages: [] }
    }),
    sendMessage: vi.fn().mockResolvedValue({
      data: {
        message: { id: 'bot1', text: '테스트 응답', type: 'bot', timestamp: new Date().toISOString() },
        chat_id: 'chat1',
        search_results: []
      }
    })
  }
}))

describe('Chat.vue 통합', () => {
  it('메시지 입력 후 전송 시 API가 호출되고, 봇 응답이 렌더링된다', async () => {
    const wrapper = mount(Chat)
    await flushPromises()
    // 채팅방을 명시적으로 선택
    if (wrapper.vm.selectChat) {
      await wrapper.vm.selectChat({ id: 'chat1', title: '테스트 채팅' })
      await flushPromises()
    }
    // 직접 메시지 전송
    wrapper.vm.newMessage = '안녕'
    await wrapper.vm.sendMessage()
    await flushPromises()
    // 상태 및 DOM 출력
    // eslint-disable-next-line no-console
    console.log('messages:', wrapper.vm.messages)
    // eslint-disable-next-line no-console
    console.log('html:', wrapper.html())
    expect(wrapper.html()).toContain('테스트 응답')
  })
})
