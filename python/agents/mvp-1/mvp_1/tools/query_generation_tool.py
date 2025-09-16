"""리포트 생성을 위한 질의를 생성하는 도구"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from google.adk.tools.function_tool import FunctionTool
import json


class QueryGenerationInput(BaseModel):
    """리포트 생성을 위한 질의 생성 입력"""
    current_step: int = Field(..., description="현재 질의 단계 (1-5)")
    user_responses: Dict[str, Any] = Field(default_factory=dict, description="이전 단계에서 사용자의 응답")
    data_schema: Dict[str, str] = Field(default_factory=dict, description="분석할 데이터의 스키마 (컬럼명: 타입)")
    data_summary: Dict[str, Any] = Field(default_factory=dict, description="분석할 데이터의 요약 통계")
    user_input: Optional[str] = Field(None, description="사용자의 현재 단계 응답")


class QueryGenerationOutput(BaseModel):
    """5단계 리포트 질의 생성 출력"""
    next_query: str = Field(..., description="사용자에게 던질 다음 질의")
    is_final_step: bool = Field(False, description="최종 단계 여부")
    report_guide: Optional[str] = Field(None, description="최종 리포트 생성 가이드 (최종 단계에서만 제공)")
    current_step: int = Field(..., description="현재 처리된 단계")
    next_step: Optional[int] = Field(None, description="다음 단계 번호 (None이면 완료)")
    collected_responses: Dict[str, Any] = Field(default_factory=dict, description="수집된 모든 사용자 응답")


@FunctionTool
def generate_report_queries(current_step: int = 1, user_responses: Dict[str, Any] = {}, data_schema: Dict[str, str] = {}, data_summary: Dict[str, Any] = {}, user_input: Optional[str] = None) -> QueryGenerationOutput:
    """
    사용자 데이터 기반으로 최적의 리포트를 생성하기 위한 5단계 질의를 단계별로 처리합니다.
    각 단계에서 사용자 응답을 받아 다음 단계로 진행하거나 최종 리포트 생성 가이드를 제공합니다.
    """
    # 사용자 응답이 있으면 현재 단계에 저장
    if user_input is not None:
        step_key = _get_step_key(current_step)
        user_responses[step_key] = user_input
    
    # 현재 단계에 따른 처리
    if current_step == 1:
        return _ask_report_type(user_responses, data_schema, data_summary)
    elif current_step == 2:
        return _ask_analysis_criteria(user_responses, data_schema, data_summary)
    elif current_step == 3:
        return _ask_data_scope_and_filtering(user_responses, data_schema, data_summary)
    elif current_step == 4:
        return _ask_report_style(user_responses, data_schema, data_summary)
    elif current_step == 5:
        return _ask_report_format(user_responses, data_schema, data_summary)
    else:
        return QueryGenerationOutput(
            next_query="모든 질의 단계가 완료되었습니다. 리포트 생성을 시작합니다.",
            is_final_step=True,
            report_guide=_generate_report_guide(user_responses),
            current_step=current_step,
            collected_responses=user_responses
        )


def _get_step_key(step: int) -> str:
    """단계 번호에 따른 응답 키를 반환합니다."""
    step_keys = {
        1: "report_type",
        2: "analysis_criteria", 
        3: "data_scope_and_filtering",
        4: "report_style",
        5: "report_format"
    }
    return step_keys.get(step, f"step_{step}")


def _ask_report_type(user_responses: Dict[str, Any], data_schema: Dict[str, str], data_summary: Dict[str, Any]) -> QueryGenerationOutput:
    """1단계: 리포트 유형을 질의합니다."""
    query = """
    어떤 종류의 리포트를 원하십니까? 다음 중 선택하거나 직접 입력해주세요:
    1. 매출 요약 (Sales Summary)
    2. 성장 분석 (Growth Analysis)
    3. 고객별 분석 (Customer Segmentation)
    4. 상품군별 성과 분석 (Product Category Performance)
    5. 지역별 성과 분석 (Regional Performance)
    6. 재고 현황 분석 (Inventory Analysis)
    7. 마케팅 성과 분석 (Marketing Performance)
    8. 고객 만족도 분석 (Customer Satisfaction)
    9. 수익성 분석 (Profitability Analysis)
    10. 트렌드 분석 (Trend Analysis)
    11. 기타 (직접 입력)
    """
    return QueryGenerationOutput(
        next_query=query,
        current_step=1,
        next_step=2,
        collected_responses=user_responses
    )


def _ask_analysis_criteria(user_responses: Dict[str, Any], data_schema: Dict[str, str], data_summary: Dict[str, Any]) -> QueryGenerationOutput:
    """2단계: 분석 기준을 질의합니다."""
    report_type = user_responses.get("report_type", "알 수 없음")
    available_columns = ", ".join(data_schema.keys()) if data_schema else "데이터 스키마 정보 없음"
    query = f"""
    '{report_type}' 리포트를 위해 데이터를 어떤 기준으로 분석할까요? 다음 중 선택하거나 직접 입력해주세요:
    1. 제품군별 (Product Category)
    2. 지역별 (Regional)
    3. 고객유형별 (Customer Type)
    4. 기간별 - 월별 (Monthly)
    5. 기간별 - 분기별 (Quarterly)
    6. 기간별 - 연간 (Annual)
    7. 매출액 구간별 (Sales Amount Range)
    8. 고객만족도별 (Customer Satisfaction Level)
    9. 거래건수별 (Transaction Count)
    10. 채널별 (Channel - 온라인/오프라인)
    11. 기타 (직접 입력)
    
    현재 데이터에는 다음과 같은 컬럼이 있습니다: {available_columns}
    """
    return QueryGenerationOutput(
        next_query=query,
        current_step=2,
        next_step=3,
        collected_responses=user_responses
    )


def _ask_data_scope_and_filtering(user_responses: Dict[str, Any], data_schema: Dict[str, str], data_summary: Dict[str, Any]) -> QueryGenerationOutput:
    """3단계: 데이터 범위 및 필터링 조건을 질의합니다."""
    analysis_criteria = user_responses.get("analysis_criteria", "알 수 없음")
    query = f"""
    '{analysis_criteria}' 기준으로 분석할 데이터의 구체적인 범위와 필터링 조건을 선택해주세요:
    1. 전체 데이터 (All Data)
    2. 최근 3개월 데이터 (Last 3 Months)
    3. 최근 6개월 데이터 (Last 6 Months)
    4. 최근 1년 데이터 (Last 1 Year)
    5. 특정 기간 지정 (Custom Date Range)
    6. 상위 10% 데이터만 (Top 10%)
    7. 상위 20% 데이터만 (Top 20%)
    8. 특정 조건 필터링 (Custom Filtering)
    9. 이상치 제외 (Exclude Outliers)
    10. 특정 값 이상/이하 (Above/Below Threshold)
    11. 기타 (직접 입력)
    
    예시: '2025년 1월부터 6월까지의 데이터', '상품군이 식품인 데이터만', '매출액 상위 10%'
    """
    return QueryGenerationOutput(
        next_query=query,
        current_step=3,
        next_step=4,
        collected_responses=user_responses
    )


def _ask_report_style(user_responses: Dict[str, Any], data_schema: Dict[str, str], data_summary: Dict[str, Any]) -> QueryGenerationOutput:
    """4단계: 리포트 스타일을 질의합니다."""
    query = """
    리포트의 스타일과 상세 수준을 어떻게 할까요? 다음 중 선택하거나 직접 입력해주세요:
    1. 간단 요약 (Summary only)
    2. 상세 분석 (Detailed analysis)
    3. 주요 지표 중심 (Key metrics focus)
    4. 그래프 및 시각화 포함 (Include charts and visualizations)
    5. 대시보드 스타일 (Dashboard style)
    6. 인사이트 중심 (Insights-focused)
    7. 비교 분석 포함 (Comparative analysis)
    8. 트렌드 분석 포함 (Trend analysis)
    9. 예측 분석 포함 (Predictive analysis)
    10. 실행 계획 포함 (Action plan included)
    11. 기타 (직접 입력)
    """
    return QueryGenerationOutput(
        next_query=query,
        current_step=4,
        next_step=5,
        collected_responses=user_responses
    )


def _ask_report_format(user_responses: Dict[str, Any], data_schema: Dict[str, str], data_summary: Dict[str, Any]) -> QueryGenerationOutput:
    """5단계: 리포트 파일 형식을 질의합니다."""
    query = """
    최종 리포트를 어떤 파일 형식으로 받으시겠습니까? 다음 중 선택하거나 직접 입력해주세요:
    1. PDF (인쇄용, 공식 문서)
    2. Excel (데이터 분석용, 편집 가능)
    3. Markdown (개발자용, 텍스트 기반)
    4. HTML (웹 브라우저용, 인터랙티브)
    5. PowerPoint (프레젠테이션용)
    6. Word (문서 편집용)
    7. CSV (데이터만 추출)
    8. JSON (구조화된 데이터)
    9. 대시보드 (웹 대시보드)
    10. 이메일 전송 (Email delivery)
    11. 기타 (직접 입력)
    """
    return QueryGenerationOutput(
        next_query=query,
        current_step=5,
        next_step=None,
        is_final_step=True,
        report_guide=_generate_report_guide(user_responses),
        collected_responses=user_responses
    )


def _generate_report_guide(user_responses: Dict[str, Any]) -> str:
    """사용자 응답을 바탕으로 최종 리포트 생성 가이드를 생성합니다."""
    report_type = user_responses.get("report_type", "지정되지 않음")
    analysis_criteria = user_responses.get("analysis_criteria", "지정되지 않음")
    data_scope = user_responses.get("data_scope_and_filtering", "지정되지 않음")
    report_style = user_responses.get("report_style", "지정되지 않음")
    report_format = user_responses.get("report_format", "지정되지 않음")

    guide = f"""
    ---
    **최종 리포트 생성 가이드:**

    **리포트 유형:** {report_type}
    **분석 기준:** {analysis_criteria}
    **데이터 범위 및 필터링:** {data_scope}
    **리포트 스타일:** {report_style}
    **파일 형식:** {report_format}

    위 정보를 바탕으로 리포트를 생성할 준비가 되었습니다.
    ---
    """
    return guide


class QueryGenerationTool:
    def __init__(self):
        self.name = "generate_report_queries"
        self.description = "사용자 데이터 기반으로 최적의 리포트를 생성하기 위한 5단계 질의를 자동 생성합니다."
        self.input_model = QueryGenerationInput
        self.output_model = QueryGenerationOutput
        self.execute = generate_report_queries