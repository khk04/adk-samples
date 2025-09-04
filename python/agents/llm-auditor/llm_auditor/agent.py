# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""LLM Auditor for verifying & refining LLM-generated answers using the web."""

from google.adk.agents import SequentialAgent

from .sub_agents.critic import critic_agent
from .sub_agents.reviser import reviser_agent


llm_auditor = SequentialAgent(
    name='llm_auditor',
    description=(
        'LLM이 생성한 답변을 평가하고, 웹을 사용하여 실제 정확성을 검증하며,'
        ' 실제 세계 지식과의 일치를 보장하기 위해 응답을 개선합니다.'
    ),
    sub_agents=[critic_agent, reviser_agent],
)

root_agent = llm_auditor
