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
from google.adk.tools.function_tool import FunctionTool
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


@FunctionTool
def generate_dynamic_query(
    current_step: int = 1,
    user_responses: Dict[str, Any] = {},
    data_analysis: Dict[str, Any] = {},
    user_input: Optional[str] = None
) -> QueryGenerationOutput:
    """
    데이터 분석 결과를 바탕으로 동적 질의를 생성합니다.
    """
    # 사용자 응답 저장
    if user_input is not None:
        step_key = _get_step_key(current_step)
        user_responses[step_key] = user_input
    
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
        return _generate_report_format_query(user_responses, data_analysis)
    else:
        return QueryGenerationOutput(
            next_query="모든 질의 단계가 완료되었습니다.",
            is_final_step=True,
            report_guide=_generate_final_guide(user_responses),
            current_step=current_step,
            collected_responses=user_responses
        )


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
    query_parts = ["데이터 분석 결과를 바탕으로 다음과 같은 리포트 유형을 추천합니다:\n"]
    
    # 데이터 분석 결과 기반 추천
    if "business_insights" in data_analysis:
        query_parts.append("📊 **추천 리포트 유형:**")
        for i, insight in enumerate(data_analysis["business_insights"][:5], 1):
            query_parts.append(f"{i}. {insight}")
    
    if "analysis_recommendations" in data_analysis:
        query_parts.append("\n🔍 **분석 권장사항:**")
        for i, rec in enumerate(data_analysis["analysis_recommendations"][:3], 1):
            query_parts.append(f"{i}. {rec}")
    
    query_parts.append("\n위 추천사항 중에서 원하는 리포트 유형을 선택하거나, 직접 원하는 분석을 설명해주세요.")
    
    return QueryGenerationOutput(
        next_query="\n".join(query_parts),
        current_step=1,
        next_step=2,
        collected_responses=user_responses
    )


def _generate_analysis_criteria_query(user_responses: Dict[str, Any], data_analysis: Dict[str, Any]) -> QueryGenerationOutput:
    """2단계: 분석 기준 질의"""
    report_type = user_responses.get("report_type", "선택된 리포트")
    
    query_parts = [f"'{report_type}' 리포트를 위한 분석 기준을 선택해주세요:\n"]
    
    # 데이터 스키마 기반 분석 기준
    if "data_summary" in data_analysis and "column_names" in data_analysis["data_summary"]:
        columns = data_analysis["data_summary"]["column_names"]
        query_parts.append("📋 **사용 가능한 분석 기준:**")
        for i, col in enumerate(columns[:8], 1):
            query_parts.append(f"{i}. {col}별 분석")
    
    query_parts.append("\n위 기준 중에서 선택하거나, 다른 분석 기준을 직접 입력해주세요.")
    
    return QueryGenerationOutput(
        next_query="\n".join(query_parts),
        current_step=2,
        next_step=3,
        collected_responses=user_responses
    )


def _generate_data_scope_query(user_responses: Dict[str, Any], data_analysis: Dict[str, Any]) -> QueryGenerationOutput:
    """3단계: 데이터 범위 질의"""
    analysis_criteria = user_responses.get("analysis_criteria", "선택된 기준")
    
    query_parts = [f"'{analysis_criteria}' 기준으로 분석할 데이터 범위를 선택해주세요:\n"]
    
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
    
    return QueryGenerationOutput(
        next_query="\n".join(query_parts),
        current_step=3,
        next_step=4,
        collected_responses=user_responses
    )


def _generate_report_style_query(user_responses: Dict[str, Any], data_analysis: Dict[str, Any]) -> QueryGenerationOutput:
    """4단계: 리포트 스타일 질의"""
    query_parts = ["리포트의 스타일과 상세 수준을 선택해주세요:\n"]
    
    query_parts.append("📊 **리포트 스타일 옵션:**")
    query_parts.append("1. 간단 요약 (핵심 지표 중심)")
    query_parts.append("2. 상세 분석 (그래프 및 시각화 포함)")
    query_parts.append("3. 대시보드 스타일 (인터랙티브)")
    query_parts.append("4. 인사이트 중심 (비즈니스 관점)")
    query_parts.append("5. 예측 분석 포함")
    
    query_parts.append("\n위 스타일 중에서 선택하거나, 원하는 스타일을 직접 설명해주세요.")
    
    return QueryGenerationOutput(
        next_query="\n".join(query_parts),
        current_step=4,
        next_step=5,
        collected_responses=user_responses
    )


def _generate_report_format_query(user_responses: Dict[str, Any], data_analysis: Dict[str, Any]) -> QueryGenerationOutput:
    """5단계: 리포트 형식 질의"""
    report_style = user_responses.get("report_style", "선택된 스타일")
    
    query_parts = [f"'{report_style}' 스타일의 리포트를 어떤 형식으로 받으시겠습니까?\n"]
    
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

query_generation_agent = Agent(
    model=MODEL,
    name="query_generation_agent",
    instruction=prompt.QUERY_GENERATION_PROMPT,
    tools=[generate_dynamic_query],
    output_key="query_results"
)