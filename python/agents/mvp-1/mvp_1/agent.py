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

"""MVP-1: Multi-agent system for data analysis and report generation with quality evaluation."""

import datetime
import uuid
from zoneinfo import ZoneInfo
from google.adk.agents import LlmAgent, LoopAgent, SequentialAgent, Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.agent_tool import AgentTool
from google.adk.models import Gemini

from . import prompt
from .sub_agents.data_analysis import data_analysis_agent
from .sub_agents.query_generation import query_generation_agent
from .sub_agents.report_generation import report_generation_agent
from .config import QUALITY_THRESHOLD, MAX_ITERATIONS, GENAI_MODEL

MODEL = "gemini-2.0-flash"


def set_session(callback_context: CallbackContext):
    """
    세션 초기화 - 고유 ID와 타임스탬프를 설정합니다.
    """
    callback_context.state["unique_id"] = str(uuid.uuid4())
    callback_context.state["timestamp"] = datetime.datetime.now(
        ZoneInfo("Asia/Seoul")
    ).isoformat()
    callback_context.state["loop_iteration"] = 0


# 데이터 분석 후 질의 생성 에이전트 (순차 실행)
data_analysis_query_agent = SequentialAgent(
    name="data_analysis_query_agent",
    description=(
        "데이터 분석 후 5단계 질의 프로세스를 완료합니다.\n"
        "1. 데이터 분석 에이전트를 호출하여 데이터 분석\n"
        "2. 질의 생성 에이전트를 호출하여 5단계 사용자 요구사항 수집 (완료될 때까지 반복)\n"
        "지원 형식: CSV, Excel"
    ),
    sub_agents=[data_analysis_agent, query_generation_agent],
)

# 리포트 생성 및 평가 에이전트
report_evaluation_agent = SequentialAgent(
    name="report_evaluation_agent", 
    description=(
        "질의 완료 후 리포트를 생성하고 품질을 평가합니다.\n"
        "1. 리포트 생성 에이전트를 호출하여 리포트 생성 및 품질 평가\n"
    ),
    sub_agents=[report_generation_agent],
)

# 전체 프로세스를 관리하는 순차 에이전트
data_analysis_report_evaluation_agent = SequentialAgent(
    name="data_analysis_report_evaluation_agent",
    description=(
        "CSV와 Excel 형식의 데이터를 분석하여 리포트를 생성하고 품질을 평가합니다.\n"
        "1. 데이터 분석 및 5단계 질의 프로세스 완료\n"
        "2. 리포트 생성 및 품질 평가\n"
        "지원 형식: CSV, Excel"
    ),
    sub_agents=[data_analysis_query_agent, report_evaluation_agent],
)


# 체커 에이전트 - 루프 종료 조건을 확인
checker_agent = Agent(
    name="checker_agent",
    model=GENAI_MODEL,
    description="리포트 품질과 반복 횟수를 확인하여 루프 종료 여부를 결정하는 에이전트",
    instruction=prompt.get_checker_prompt(QUALITY_THRESHOLD, MAX_ITERATIONS),
    tools=[],  # 조건 확인은 상태에서 직접 처리
    output_key="checker_output",
)


# 메인 루프 에이전트 - 품질 기준을 만족할 때까지 반복 (최대 3회)
mvp_coordinator = LoopAgent(
    name="mvp_coordinator",
    description=(
        "사용자 데이터를 기반으로 고품질 리포트를 생성하는 멀티 에이전트 시스템.\n"
        "데이터 분석, 질의 생성, 리포트 생성을 담당하는 전문 서브 에이전트들을 조율하여 "
        "사용자 맞춤형 리포트를 제공합니다. 품질 기준을 만족할 때까지 반복 실행하며,\n"
        "최대 3회 반복으로 무한 루프를 방지합니다."
    ),
    sub_agents=[
        data_analysis_report_evaluation_agent,  # 데이터 분석, 질의 생성, 리포트 생성 및 평가
        checker_agent,                          # 조건 확인 및 루프 종료 결정
    ],
    max_iterations=MAX_ITERATIONS,  # config.py에서 정의된 최대 반복 횟수 (기본값: 3)
    before_agent_callback=set_session,
)

root_agent = mvp_coordinator