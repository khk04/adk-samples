// @vitest-environment jsdom
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ChatInput from '../ChatInput.vue'

describe('ChatInput.vue', () => {
  it('입력값이 변경되면 v-model로 반영된다', async () => {
    const wrapper = mount(ChatInput, {
      props: {
        modelValue: '',
      },
    })
    const textarea = wrapper.find('textarea')
    await textarea.setValue('테스트 입력')
    expect(wrapper.emitted()['update:modelValue'][0]).toEqual(['테스트 입력'])
  })

  it('handleSend 호출 시 send 이벤트가 emit된다', async () => {
    const wrapper = mount(ChatInput, {
      props: {
        modelValue: '테스트',
      },
    })
    // 직접 메서드 호출
    wrapper.vm.handleSend()
    expect(wrapper.emitted().send).toBeTruthy()
  })
})
