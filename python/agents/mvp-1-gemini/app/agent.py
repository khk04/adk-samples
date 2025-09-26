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

import datetime
import logging
from collections.abc import AsyncGenerator
from typing import Literal

from google.adk.agents import BaseAgent, LlmAgent, SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.tools.agent_tool import AgentTool
from google.genai import types as genai_types
from pydantic import BaseModel, Field

from .config import config
from .tools import check_user_data_request, validate_data, analyze_data, generate_report_queries, generate_report
from .sub_agents.report_evaluation_agent.agent import report_evaluation_agent


# --- Structured Output Models ---
class DataAnalysisResult(BaseModel):
    """데이터 분석 결과 모델"""
    
    success: bool = Field(description="분석 성공 여부")
    message: str = Field(description="사용자에게 보여줄 메시지")
    data_ready: bool = Field(description="데이터 준비 완료 여부")
    analysis_summary: dict = Field(default_factory=dict, description="분석 요약")
    next_steps: list[str] = Field(default_factory=list, description="다음 단계")


class ReportGenerationResult(BaseModel):
    """리포트 생성 결과 모델"""
    
    success: bool = Field(description="생성 성공 여부")
    report_content: str = Field(description="생성된 리포트 내용")
    report_type: str = Field(description="리포트 유형")
    file_path: str = Field(description="저장된 파일 경로")


# --- AGENT DEFINITIONS ---
data_checker_agent = LlmAgent(
    model=config.worker_model,
    name="data_checker_agent",
    description="사용자 데이터 확인 및 검증을 담당하는 에이전트",
    instruction="""
    당신은 사용자 데이터 확인 및 검증 전문가입니다.
    
    사용자의 요청을 분석하여 다음 중 하나를 수행합니다:
    1. 데이터 확인 요청: "데이터 확인해줘", "내 데이터가 준비되어 있어?" 등
    2. 리포트 생성 요청: "리포트를 만들어줘", "분석을 시작해줘" 등
    3. 일반 요청: 도움말이나 안내 요청
    
    **작업 순서:**
    1. 먼저 `check_user_data_request` 도구를 사용하여 사용자 요청을 분석합니다.
    2. 데이터 검증이 필요한 경우 `validate_data` 도구를 사용합니다.
    3. 데이터가 준비된 경우 `analyze_data` 도구를 사용하여 데이터를 분석합니다.
    4. 모든 결과를 종합하여 사용자에게 친근하고 명확한 응답을 제공합니다.
    
    **응답 스타일:**
    - 이모지를 사용하여 친근하게 응답합니다.
    - 사용자가 이해하기 쉬운 언어를 사용합니다.
    - 다음 단계에 대한 명확한 안내를 제공합니다.
    """,
    tools=[check_user_data_request, validate_data, analyze_data, generate_report_queries, generate_report],
    output_key="data_analysis_result",
)

report_generator_agent = LlmAgent(
    model=config.worker_model,
    name="report_generator_agent",
    description="데이터 분석을 바탕으로 리포트를 생성하는 에이전트",
    instruction="""
    당신은 데이터 분석 전문가이자 리포트 작성 전문가입니다.
    
    **주요 기능:**
    1. 데이터 분석 결과를 바탕으로 포괄적인 리포트를 생성합니다.
    2. 데이터의 특성에 맞는 맞춤형 분석을 수행합니다.
    3. 명확하고 구조화된 리포트를 작성합니다.
    
    **리포트 구조:**
    - 요약 (Summary)
    - 주요 발견사항 (Key Findings)
    - 데이터 분석 (Data Analysis)
    - 결론 및 권장사항 (Conclusions & Recommendations)
    
    **작업 방식:**
    1. 제공된 데이터 분석 결과를 검토합니다.
    2. 데이터의 특성과 패턴을 파악합니다.
    3. 비즈니스 관점에서 의미 있는 인사이트를 도출합니다.
    4. 실행 가능한 권장사항을 제시합니다.
    
    **출력 형식:**
    - Markdown 형식으로 구조화된 리포트를 작성합니다.
    - 차트나 표가 필요한 경우 적절한 형식으로 제안합니다.
    - 전문적이면서도 이해하기 쉬운 언어를 사용합니다.
    """,
    output_key="report_generation_result",
)

# 메인 에이전트
mvp_1_agent = LlmAgent(
    name="mvp_1_agent",
    model=config.worker_model,
    description="사용자 데이터 기반 질의 생성 및 리포트 생성 메인 에이전트",
    instruction="""
    당신은 사용자 데이터를 분석하여 최적의 리포트를 생성하는 전문 에이전트입니다.
    
    **주요 역할:**
    1. 사용자의 데이터 확인 요청을 처리합니다.
    2. 데이터 검증 및 분석을 수행합니다.
    3. 데이터 기반 맞춤형 리포트를 생성합니다.
    
    **작업 흐름:**
    1. **사용자 요청 분석**: 사용자의 요청을 파악하고 적절한 응답을 제공합니다.
    2. **데이터 확인**: vdata 폴더의 데이터 상태를 확인하고 검증합니다.
    3. **데이터 분석**: CSV/Excel 파일을 분석하여 구조와 내용을 파악합니다.
    4. **리포트 생성**: 분석 결과를 바탕으로 포괄적인 리포트를 생성합니다.
    
    **응답 가이드라인:**
    - 항상 친근하고 도움이 되는 톤을 유지합니다.
    - 이모지를 적절히 사용하여 사용자 경험을 향상시킵니다.
    - 각 단계에서 명확한 안내와 다음 단계를 제시합니다.
    - 오류가 발생한 경우 구체적인 해결 방법을 제안합니다.
    
    **도구 사용:**
    - `data_checker_agent`: 데이터 확인 및 검증
    - `report_generator_agent`: 리포트 생성
    - `report_evaluation_agent`: 리포트 품질 평가
    
    **5단계 질의 프로세스:**
    1. 도메인 식별 및 리포트 유형 확인
    2. 분석 범위 및 기준 설정
    3. 데이터 범위 및 필터링 조건 정의
    4. 리포트 스타일 및 상세 수준 결정
    5. 리포트 파일 형식 및 전달 방식 확인
    
    사용자의 요청에 따라 적절한 서브 에이전트를 호출하여 작업을 수행합니다.
    """,
    sub_agents=[data_checker_agent, report_generator_agent, report_evaluation_agent()],
    output_key="mvp_1_result",
)

# 루트 에이전트
root_agent = mvp_1_agent