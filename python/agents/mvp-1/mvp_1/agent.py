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

"""MVP-1: Multi-agent system for user data analysis and report generation."""

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

from . import prompt
from .sub_agents.data_analysis import data_analysis_agent
from .sub_agents.query_generation import query_generation_agent
from .sub_agents.report_generation import report_generation_agent

MODEL = "gemini-2.0-flash"


mvp_coordinator = LlmAgent(
    name="mvp_coordinator",
    model=MODEL,
    description=(
        "사용자 데이터를 분석하여 최적의 비즈니스 리포트를 생성하는 멀티 에이전트 시스템. "
        "데이터 분석, 질의 생성, 리포트 생성을 담당하는 전문 서브 에이전트들을 조율하여 "
        "사용자 맞춤형 리포트를 제공합니다."
    ),
    instruction=prompt.MVP_COORDINATOR_PROMPT,
    output_key="final_report",
    tools=[
        AgentTool(agent=data_analysis_agent),
        AgentTool(agent=query_generation_agent),
        AgentTool(agent=report_generation_agent),
    ],
)

root_agent = mvp_coordinator