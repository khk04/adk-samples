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

"""Query generation sub-agent for creating dynamic queries."""

from google.adk import Agent
from google.adk.agents import LoopAgent
from google.adk.tools.function_tool import FunctionTool
from google.adk.agents.callback_context import CallbackContext
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from . import prompt


class QueryGenerationInput(BaseModel):
    """질의 생성 입력"""
    current_step: int = Field(..., description="현재 질의 단계 (1-5)")
    user_responses: Dict[str, Any] = Field(default_factory=dict, description="이전 단계 사용자 응답")
    data_analysis: Dict[str, Any] = Field(default_factory=dict, description="데이터 분석 결과")
    user_input: Optional[str] = Field(None, description="현재 단계 사용자 응답")


class QueryGenerationOutput(BaseModel):
    """질의 생성 출력"""
    next_query: str = Field(..., description="다음 질의")
    is_final_step: bool = Field(False, description="최종 단계 여부")
    report_guide: Optional[str] = Field(None, description="최종 리포트 생성 가이드")
    current_step: int = Field(..., description="현재 단계")
    next_step: Optional[int] = Field(None, description="다음 단계")
    collected_responses: Dict[str, Any] = Field(default_factory=dict, description="수집된 응답")


def initialize_query_session(callback_context: CallbackContext):
    """질의 세션 초기화 - 단계 및 상태 추적"""
    if "query_step" not in callback_context.state:
        callback_context.state["query_step"] = 1
        callback_context.state["user_responses"] = {}
        callback_context.state["query_completed"] = False
        callback_context.state["max_step"] = 5  # 총 5단계
        callback_context.state["should_exit_query_loop"] = False  # 루프 종료 플래그
        
    print(f"[Query Session] 초기화 완료 - 현재 단계: {callback_context.state.get('query_step', 1)}/5")


@FunctionTool
def generate_dynamic_query(
    current_step: int = 1,
    user_responses: Dict[str, Any] = {},
    data_analysis: Dict[str, Any] = {},
    user_input: Optional[str] = None
) -> QueryGenerationOutput:
    """
    데이터 분석 결과를 바탕으로 동적 질의를 생성합니다.
    5단계를 모두 완료하면 루프 종료 신호를 상태에 설정합니다.
    """
    # 사용자 응답 저장 (현재 단계가 1보다 클 때만)
    if user_input is not None and current_step > 1:
        prev_step_key = _get_step_key(current_step - 1)
        user_responses[prev_step_key] = user_input
    
    # 5단계 완료 확인
    if current_step > 5:
        # 5단계 완료 상태 설정
        return QueryGenerationOutput(
            next_query="🎉 5단계 질의가 모두 완료되었습니다! 이제 리포트를 생성하겠습니다.",
            is_final_step=True,
            report_guide=_generate_final_guide(user_responses),
            current_step=current_step,
            collected_responses=user_responses
        )
    
    # 단계별 질의 생성
    if current_step == 1:
        return _generate_report_type_query(user_responses, data_analysis)
    elif current_step == 2:
        return _generate_analysis_criteria_query(user_responses, data_analysis)
    elif current_step == 3:
        return _generate_data_scope_query(user_responses, data_analysis)
    elif current_step == 4:
        return _generate_report_style_query(user_responses, data_analysis)
    elif current_step == 5:
        # 5단계에서는 응답을 저장하고 완료 표시
        if user_input is not None:
            user_responses["report_format"] = user_input
        
        result = _generate_report_format_query(user_responses, data_analysis)
        
        # 5단계 완료시 상태 업데이트
        return result
    else:
        # 예외 상황
        return QueryGenerationOutput(
            next_query="오류가 발생했습니다. 다시 시도해주세요.",
            is_final_step=False,
            current_step=1,
            collected_responses=user_responses
        )


@FunctionTool
def escalate_query_completion(
    is_completed: bool = False,
    step_count: int = 0,
    collected_responses: Dict[str, Any] = {}
) -> dict:
    """
    5단계 질의가 완료되면 루프 종료 신호를 발생시킵니다.
    상태를 통해 루프 종료 조건을 제어합니다.
    """
    if is_completed and step_count >= 5:
        # 모든 필수 응답이 수집되었는지 확인
        required_keys = ["report_type", "analysis_criteria", "data_scope", "report_style", "report_format"]
        all_collected = all(key in collected_responses for key in required_keys)
        
        if all_collected:
            return {
                "status": "COMPLETED",
                "message": "🎉 5단계 질의가 모두 완료되었습니다! 루프를 종료하고 다음 에이전트로 진행합니다.",
                "should_exit_loop": True,  # 루프 종료 플래그
                "step_count": step_count,
                "collected_responses": collected_responses
            }
    
    return {
        "status": "CONTINUE",
        "message": f"질의 진행 중... (현재 {step_count}/5 단계)",
        "should_exit_loop": False,  # 루프 계속
        "step_count": step_count
    }


@FunctionTool
def check_query_completion() -> dict:
    """질의 완료 상태를 확인합니다."""
    return {
        "status": "checking",
        "message": "질의 완료 상태를 확인합니다."
    }


def _get_step_key(step: int) -> str:
    """단계별 키 반환"""
    step_keys = {
        1: "report_type",
        2: "analysis_criteria",
        3: "data_scope",
        4: "report_style",
        5: "report_format"
    }
    return step_keys.get(step, f"step_{step}")


def _generate_report_type_query(user_responses: Dict[str, Any], data_analysis: Dict[str, Any]) -> QueryGenerationOutput:
    """1단계: 리포트 유형 질의"""
    query_parts = ["📊 **1단계: 리포트 유형 선택**\n"]
    query_parts.append("데이터 분석 결과를 바탕으로 다음과 같은 리포트 유형을 추천합니다:\n")
    
    # 데이터 분석 결과 기반 추천
    if "business_insights" in data_analysis:
        query_parts.append("� **추천 리포트 유형:**")
        for i, insight in enumerate(data_analysis["business_insights"][:5], 1):
            query_parts.append(f"{i}. {insight}")
    
    if "analysis_recommendations" in data_analysis:
        query_parts.append("\n🔍 **분석 권장사항:**")
        for i, rec in enumerate(data_analysis["analysis_recommendations"][:3], 1):
            query_parts.append(f"{i}. {rec}")
    
    query_parts.append("\n위 추천사항 중에서 원하는 리포트 유형을 선택하거나, 직접 원하는 분석을 설명해주세요.")
    query_parts.append("(1단계/5단계)")
    
    return QueryGenerationOutput(
        next_query="\n".join(query_parts),
        current_step=1,
        next_step=2,
        is_final_step=False,
        collected_responses=user_responses
    )


def _generate_analysis_criteria_query(user_responses: Dict[str, Any], data_analysis: Dict[str, Any]) -> QueryGenerationOutput:
    """2단계: 분석 기준 질의"""
    report_type = user_responses.get("report_type", "선택된 리포트")
    
    query_parts = [f"📊 **2단계: 분석 기준 선택**\n"]
    query_parts.append(f"'{report_type}' 리포트를 위한 분석 기준을 선택해주세요:\n")
    
    # 데이터 스키마 기반 분석 기준
    if "data_summary" in data_analysis and "column_names" in data_analysis["data_summary"]:
        columns = data_analysis["data_summary"]["column_names"]
        query_parts.append("📋 **사용 가능한 분석 기준:**")
        for i, col in enumerate(columns[:8], 1):
            query_parts.append(f"{i}. {col}별 분석")
    
    query_parts.append("\n위 기준 중에서 선택하거나, 다른 분석 기준을 직접 입력해주세요.")
    query_parts.append("(2단계/5단계)")
    
    return QueryGenerationOutput(
        next_query="\n".join(query_parts),
        current_step=2,
        next_step=3,
        is_final_step=False,
        collected_responses=user_responses
    )


def _generate_data_scope_query(user_responses: Dict[str, Any], data_analysis: Dict[str, Any]) -> QueryGenerationOutput:
    """3단계: 데이터 범위 질의"""
    analysis_criteria = user_responses.get("analysis_criteria", "선택된 기준")
    
    query_parts = [f"📊 **3단계: 데이터 범위 선택**\n"]
    query_parts.append(f"'{analysis_criteria}' 기준으로 분석할 데이터 범위를 선택해주세요:\n")
    
    # 데이터 크기 기반 추천
    if "data_summary" in data_analysis and "total_rows" in data_analysis["data_summary"]:
        total_rows = data_analysis["data_summary"]["total_rows"]
        if total_rows > 10000:
            query_parts.append("📊 **대용량 데이터 추천:**")
            query_parts.append("1. 최근 3개월 데이터")
            query_parts.append("2. 상위 20% 데이터")
            query_parts.append("3. 샘플링된 데이터")
        else:
            query_parts.append("📊 **전체 데이터 분석 가능:**")
            query_parts.append("1. 전체 데이터")
            query_parts.append("2. 특정 기간 데이터")
            query_parts.append("3. 조건별 필터링")
    
    query_parts.append("\n위 옵션 중에서 선택하거나, 구체적인 범위를 직접 입력해주세요.")
    query_parts.append("(3단계/5단계)")
    
    return QueryGenerationOutput(
        next_query="\n".join(query_parts),
        current_step=3,
        next_step=4,
        is_final_step=False,
        collected_responses=user_responses
    )


def _generate_report_style_query(user_responses: Dict[str, Any], data_analysis: Dict[str, Any]) -> QueryGenerationOutput:
    """4단계: 리포트 스타일 질의"""
    query_parts = ["📊 **4단계: 리포트 스타일 선택**\n"]
    query_parts.append("리포트의 스타일과 상세 수준을 선택해주세요:\n")
    
    query_parts.append("📊 **리포트 스타일 옵션:**")
    query_parts.append("1. 간단 요약 (핵심 지표 중심)")
    query_parts.append("2. 상세 분석 (그래프 및 시각화 포함)")
    query_parts.append("3. 대시보드 스타일 (인터랙티브)")
    query_parts.append("4. 인사이트 중심 (비즈니스 관점)")
    query_parts.append("5. 예측 분석 포함")
    
    query_parts.append("\n위 스타일 중에서 선택하거나, 원하는 스타일을 직접 설명해주세요.")
    query_parts.append("(4단계/5단계)")
    
    return QueryGenerationOutput(
        next_query="\n".join(query_parts),
        current_step=4,
        next_step=5,
        is_final_step=False,
        collected_responses=user_responses
    )


def _generate_report_format_query(user_responses: Dict[str, Any], data_analysis: Dict[str, Any]) -> QueryGenerationOutput:
    """5단계: 리포트 형식 질의 (최종 단계)"""
    report_style = user_responses.get("report_style", "선택된 스타일")
    
    query_parts = [f"📊 **5단계: 파일 형식 선택 (최종 단계)**\n"]
    query_parts.append(f"'{report_style}' 스타일의 리포트를 어떤 형식으로 받으시겠습니까?\n")
    
    query_parts.append("📤 **파일 형식 옵션:**")
    query_parts.append("1. PDF (인쇄용)")
    query_parts.append("2. Excel (데이터 편집 가능)")
    query_parts.append("3. HTML (웹 브라우저용)")
    query_parts.append("4. PowerPoint (프레젠테이션용)")
    query_parts.append("5. Markdown (개발자용)")
    
    query_parts.append("\n📧 **전달 방식:**")
    query_parts.append("6. 이메일 전송")
    query_parts.append("7. 파일 다운로드")
    query_parts.append("8. 웹 대시보드")
    
    query_parts.append("\n위 형식 중에서 선택하거나, 다른 형식을 직접 입력해주세요.")
    query_parts.append("(5단계/5단계 - 최종)")
    
    return QueryGenerationOutput(
        next_query="\n".join(query_parts),
        current_step=5,
        next_step=None,
        is_final_step=True,
        report_guide=_generate_final_guide(user_responses),
        collected_responses=user_responses
    )


def _generate_final_guide(user_responses: Dict[str, Any]) -> str:
    """최종 리포트 생성 가이드"""
    report_type = user_responses.get("report_type", "지정되지 않음")
    analysis_criteria = user_responses.get("analysis_criteria", "지정되지 않음")
    data_scope = user_responses.get("data_scope", "지정되지 않음")
    report_style = user_responses.get("report_style", "지정되지 않음")
    report_format = user_responses.get("report_format", "지정되지 않음")

    guide = f"""
---
**최종 리포트 생성 가이드:**

**리포트 유형:** {report_type}
**분석 기준:** {analysis_criteria}
**데이터 범위:** {data_scope}
**리포트 스타일:** {report_style}
**파일 형식:** {report_format}

위 정보를 바탕으로 리포트를 생성할 준비가 되었습니다.
---
"""
    return guide


MODEL = "gemini-2.0-flash"

# 질의 처리 에이전트 - 단일 질의 처리
query_processor_agent = Agent(
    model=MODEL,
    name="query_processor_agent",
    instruction=prompt.QUERY_GENERATION_PROMPT,
    tools=[generate_dynamic_query, escalate_query_completion],  # escalate 함수 추가
    output_key="query_step_result"
)

# 질의 완료 체커 에이전트 - 간단한 종료 조건 확인
query_checker_agent = Agent(
    model=MODEL,
    name="query_checker_agent",
    instruction="""
당신은 5단계 질의 생성 완료 상태를 확인하는 전문가입니다.

**주요 역할:**
1. 질의 단계 진행 상황 모니터링
2. 5단계 완료 여부 확인
3. 루프 종료 조건 확인

**루프 종료 조건:**
- 5단계 완료 및 is_final_step=True 확인
- 모든 사용자 응답 수집 완료 확인

escalate_query_completion 함수를 사용하여 상태를 확인하세요.
이 함수가 should_exit_loop=True를 반환하면 루프를 종료합니다.
""",
    tools=[escalate_query_completion, check_query_completion],
    output_key="query_completion_status"
)

# 질의 생성 루프 에이전트 - 5단계가 완료될 때까지 반복 (최대 10회 제한)
query_generation_agent = LoopAgent(
    name="query_generation_agent",
    description=(
        "5단계 질의 프로세스를 완료할 때까지 반복 실행하는 질의 생성 에이전트.\n"
        "1단계부터 5단계까지 순차적으로 사용자 요구사항을 수집하고,\n"
        "모든 단계가 완료되거나 escalate 시그널 수신시 다음 에이전트로 진행됩니다.\n"
        "최대 10회 반복으로 무한 루프를 방지합니다."
    ),
    sub_agents=[
        query_processor_agent,  # 질의 처리
        query_checker_agent,    # 완료 상태 확인 및 escalate 처리
    ],
    max_iterations=3,  # 최대 10회 반복으로 무한 루프 방지
    before_agent_callback=initialize_query_session,
)