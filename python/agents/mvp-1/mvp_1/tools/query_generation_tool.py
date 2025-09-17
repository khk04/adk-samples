"""리포트 생성을 위한 질의를 생성하는 도구"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from google.adk.tools.function_tool import FunctionTool
import json
import re


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
            next_query="모든 질의 단계가 완료되었습니다. 수집된 정보를 바탕으로 리포트를 생성할 준비가 되었습니다. 리포트 생성을 진행하시겠습니까? (예/아니요)",
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


def _analyze_data_schema(data_schema: Dict[str, str]) -> Dict[str, Any]:
    """데이터 스키마를 분석하여 컬럼의 의미와 분석 가능성을 파악합니다."""
    analysis = {
        "categorical_columns": [],
        "numerical_columns": [],
        "date_columns": [],
        "text_columns": [],
        "business_insights": [],
        "potential_analyses": []
    }
    
    for column, dtype in data_schema.items():
        column_lower = column.lower()
        
        # 데이터 타입별 분류
        if dtype in ['object', 'string', 'category']:
            if any(keyword in column_lower for keyword in ['date', 'time', 'created', 'updated']):
                analysis["date_columns"].append(column)
            elif any(keyword in column_lower for keyword in ['name', 'description', 'comment', 'note']):
                analysis["text_columns"].append(column)
            else:
                analysis["categorical_columns"].append(column)
        elif dtype in ['int64', 'float64', 'int32', 'float32', 'number']:
            analysis["numerical_columns"].append(column)
    
    # 비즈니스 인사이트 도출
    for column in analysis["categorical_columns"]:
        column_lower = column.lower()
        if any(keyword in column_lower for keyword in ['product', 'category', 'item']):
            analysis["business_insights"].append(f"제품군별 분석 가능: {column}")
        elif any(keyword in column_lower for keyword in ['region', 'area', 'location', 'city', 'country']):
            analysis["business_insights"].append(f"지역별 분석 가능: {column}")
        elif any(keyword in column_lower for keyword in ['customer', 'client', 'user']):
            analysis["business_insights"].append(f"고객별 분석 가능: {column}")
        elif any(keyword in column_lower for keyword in ['channel', 'source', 'platform']):
            analysis["business_insights"].append(f"채널별 분석 가능: {column}")
    
    for column in analysis["numerical_columns"]:
        column_lower = column.lower()
        if any(keyword in column_lower for keyword in ['sales', 'revenue', 'amount', 'price', 'cost']):
            analysis["business_insights"].append(f"매출/수익 분석 가능: {column}")
        elif any(keyword in column_lower for keyword in ['quantity', 'count', 'number', 'volume']):
            analysis["business_insights"].append(f"수량 분석 가능: {column}")
        elif any(keyword in column_lower for keyword in ['rating', 'score', 'satisfaction']):
            analysis["business_insights"].append(f"평가/만족도 분석 가능: {column}")
    
    # 잠재적 분석 유형 도출
    if analysis["date_columns"]:
        analysis["potential_analyses"].append("시계열 분석 (트렌드, 계절성)")
    if len(analysis["numerical_columns"]) >= 2:
        analysis["potential_analyses"].append("상관관계 분석")
    if analysis["categorical_columns"] and analysis["numerical_columns"]:
        analysis["potential_analyses"].append("그룹별 성과 분석")
    if analysis["numerical_columns"]:
        analysis["potential_analyses"].append("통계적 요약 및 분포 분석")
    
    return analysis


def _analyze_data_summary(data_summary: Dict[str, Any]) -> Dict[str, Any]:
    """데이터 요약 통계를 분석하여 인사이트를 도출합니다."""
    insights = {
        "data_characteristics": [],
        "notable_patterns": [],
        "recommendations": []
    }
    
    # 데이터 크기 분석
    if "total_rows" in data_summary:
        total_rows = data_summary["total_rows"]
        if total_rows > 100000:
            insights["data_characteristics"].append(f"대용량 데이터셋 ({total_rows:,}행) - 샘플링 고려 필요")
        elif total_rows > 10000:
            insights["data_characteristics"].append(f"중간 규모 데이터셋 ({total_rows:,}행) - 전체 분석 가능")
        else:
            insights["data_characteristics"].append(f"소규모 데이터셋 ({total_rows:,}행) - 상세 분석 가능")
    
    # 결측값 분석
    if "missing_values" in data_summary:
        missing_data = data_summary["missing_values"]
        high_missing = [col for col, count in missing_data.items() if count > 0]
        if high_missing:
            insights["notable_patterns"].append(f"결측값이 있는 컬럼: {', '.join(high_missing)}")
            insights["recommendations"].append("결측값 처리 방안 필요")
    
    # 수치형 데이터 분포 분석
    if "numeric_stats" in data_summary:
        numeric_stats = data_summary["numeric_stats"]
        for column, stats in numeric_stats.items():
            if "std" in stats and "mean" in stats:
                cv = stats["std"] / stats["mean"] if stats["mean"] != 0 else 0
                if cv > 1:
                    insights["notable_patterns"].append(f"{column}: 높은 변동성 (CV={cv:.2f})")
                elif cv < 0.1:
                    insights["notable_patterns"].append(f"{column}: 낮은 변동성 (CV={cv:.2f})")
    
    # 범주형 데이터 분석
    if "categorical_stats" in data_summary:
        categorical_stats = data_summary["categorical_stats"]
        for column, stats in categorical_stats.items():
            if "unique_count" in stats:
                unique_count = stats["unique_count"]
                if unique_count > 50:
                    insights["notable_patterns"].append(f"{column}: 높은 다양성 ({unique_count}개 고유값)")
                elif unique_count < 5:
                    insights["notable_patterns"].append(f"{column}: 낮은 다양성 ({unique_count}개 고유값)")
    
    return insights


def _generate_dynamic_query(step: int, user_responses: Dict[str, Any], 
                          data_schema: Dict[str, str], data_summary: Dict[str, Any]) -> str:
    """데이터 분석 결과를 바탕으로 동적 질의를 생성합니다."""
    
    schema_analysis = _analyze_data_schema(data_schema)
    summary_analysis = _analyze_data_summary(data_summary)
    
    if step == 1:
        return _generate_report_type_query(schema_analysis, summary_analysis)
    elif step == 2:
        return _generate_analysis_criteria_query(user_responses, schema_analysis, summary_analysis)
    elif step == 3:
        return _generate_data_scope_query(user_responses, schema_analysis, summary_analysis)
    elif step == 4:
        return _generate_report_style_query(user_responses, schema_analysis, summary_analysis)
    elif step == 5:
        return _generate_report_format_query(user_responses, schema_analysis, summary_analysis)
    else:
        return "모든 질의 단계가 완료되었습니다."


def _generate_report_type_query(schema_analysis: Dict[str, Any], summary_analysis: Dict[str, Any]) -> str:
    """1단계: 데이터 기반 리포트 유형 질의 생성"""
    query_parts = ["데이터를 분석한 결과, 다음과 같은 리포트 유형을 추천합니다:\n"]
    
    # 비즈니스 인사이트 기반 추천
    if schema_analysis["business_insights"]:
        query_parts.append("📊 **추천 리포트 유형:**")
        for i, insight in enumerate(schema_analysis["business_insights"][:5], 1):
            query_parts.append(f"{i}. {insight}")
    
    # 잠재적 분석 기반 추천
    if schema_analysis["potential_analyses"]:
        query_parts.append("\n🔍 **가능한 분석 유형:**")
        for i, analysis in enumerate(schema_analysis["potential_analyses"], 1):
            query_parts.append(f"{i}. {analysis}")
    
    # 데이터 특성 기반 추천
    if summary_analysis["data_characteristics"]:
        query_parts.append("\n💡 **데이터 특성:**")
        for characteristic in summary_analysis["data_characteristics"]:
            query_parts.append(f"- {characteristic}")
    
    query_parts.append("\n위 추천사항 중에서 원하는 리포트 유형을 선택하거나, 직접 원하는 분석을 설명해주세요.")
    
    return "\n".join(query_parts)


def _generate_analysis_criteria_query(user_responses: Dict[str, Any], 
                                    schema_analysis: Dict[str, Any], 
                                    summary_analysis: Dict[str, Any]) -> str:
    """2단계: 데이터 기반 분석 기준 질의 생성"""
    report_type = user_responses.get("report_type", "선택된 리포트")
    
    query_parts = [f"'{report_type}' 리포트를 위한 분석 기준을 선택해주세요:\n"]
    
    # 사용 가능한 컬럼 기반 분석 기준
    if schema_analysis["categorical_columns"]:
        query_parts.append("📋 **범주별 분석 기준:**")
        for i, column in enumerate(schema_analysis["categorical_columns"][:5], 1):
            query_parts.append(f"{i}. {column}별 분석")
    
    if schema_analysis["numerical_columns"]:
        query_parts.append("\n📊 **수치별 분석 기준:**")
        for i, column in enumerate(schema_analysis["numerical_columns"][:5], 1):
            query_parts.append(f"{i}. {column} 기준 분석")
    
    if schema_analysis["date_columns"]:
        query_parts.append("\n📅 **시간별 분석 기준:**")
        for i, column in enumerate(schema_analysis["date_columns"], 1):
            query_parts.append(f"{i}. {column} 기준 시계열 분석")
    
    # 데이터 패턴 기반 추천
    if summary_analysis["notable_patterns"]:
        query_parts.append("\n🎯 **데이터 패턴 기반 추천:**")
        for i, pattern in enumerate(summary_analysis["notable_patterns"][:3], 1):
            query_parts.append(f"{i}. {pattern} 관련 분석")
    
    query_parts.append("\n위 기준 중에서 선택하거나, 다른 분석 기준을 직접 입력해주세요.")
    
    return "\n".join(query_parts)


def _generate_data_scope_query(user_responses: Dict[str, Any], 
                             schema_analysis: Dict[str, Any], 
                             summary_analysis: Dict[str, Any]) -> str:
    """3단계: 데이터 범위 및 필터링 질의 생성"""
    analysis_criteria = user_responses.get("analysis_criteria", "선택된 기준")
    
    query_parts = [f"'{analysis_criteria}' 기준으로 분석할 데이터 범위를 선택해주세요:\n"]
    
    # 데이터 크기 기반 추천
    if summary_analysis.get("data_characteristics"):
        for characteristic in summary_analysis["data_characteristics"]:
            if "대용량" in characteristic:
                query_parts.append("📊 **대용량 데이터 추천:**")
                query_parts.append("1. 최근 3개월 데이터 (성능 최적화)")
                query_parts.append("2. 상위 20% 데이터 (핵심 데이터)")
                query_parts.append("3. 샘플링된 데이터 (전체 패턴 분석)")
                break
            elif "중간 규모" in characteristic or "소규모" in characteristic:
                query_parts.append("📊 **전체 데이터 분석 가능:**")
                query_parts.append("1. 전체 데이터")
                query_parts.append("2. 특정 기간 데이터")
                query_parts.append("3. 조건별 필터링")
                break
    
    # 날짜 컬럼이 있는 경우
    if schema_analysis["date_columns"]:
        query_parts.append(f"\n📅 **시간 범위 선택:**")
        query_parts.append("1. 최근 1개월")
        query_parts.append("2. 최근 3개월") 
        query_parts.append("3. 최근 6개월")
        query_parts.append("4. 최근 1년")
        query_parts.append("5. 특정 기간 지정")
    
    # 수치형 데이터가 있는 경우
    if schema_analysis["numerical_columns"]:
        query_parts.append(f"\n🔢 **수치 기준 필터링:**")
        query_parts.append("1. 상위 10% 데이터")
        query_parts.append("2. 상위 25% 데이터")
        query_parts.append("3. 특정 값 이상/이하")
        query_parts.append("4. 이상치 제외")
    
    # 결측값이 있는 경우
    if summary_analysis.get("notable_patterns"):
        missing_patterns = [p for p in summary_analysis["notable_patterns"] if "결측값" in p]
        if missing_patterns:
            query_parts.append(f"\n⚠️ **데이터 품질 고려:**")
            query_parts.append("1. 결측값 제외")
            query_parts.append("2. 결측값 포함")
            query_parts.append("3. 결측값 대체")
    
    query_parts.append("\n위 옵션 중에서 선택하거나, 구체적인 범위를 직접 입력해주세요.")
    
    return "\n".join(query_parts)


def _generate_report_style_query(user_responses: Dict[str, Any], 
                               schema_analysis: Dict[str, Any], 
                               summary_analysis: Dict[str, Any]) -> str:
    """4단계: 리포트 스타일 질의 생성"""
    query_parts = ["리포트의 스타일과 상세 수준을 선택해주세요:\n"]
    
    # 데이터 크기 기반 스타일 추천
    if summary_analysis.get("data_characteristics"):
        for characteristic in summary_analysis["data_characteristics"]:
            if "대용량" in characteristic:
                query_parts.append("📊 **대용량 데이터 추천 스타일:**")
                query_parts.append("1. 핵심 지표 중심 요약")
                query_parts.append("2. 대시보드 스타일")
                query_parts.append("3. 주요 트렌드 위주")
                break
            elif "중간 규모" in characteristic:
                query_parts.append("📊 **중간 규모 데이터 추천 스타일:**")
                query_parts.append("1. 상세 분석 + 요약")
                query_parts.append("2. 그래프 및 시각화 포함")
                query_parts.append("3. 비교 분석 포함")
                break
            else:
                query_parts.append("📊 **소규모 데이터 추천 스타일:**")
                query_parts.append("1. 상세 분석")
                query_parts.append("2. 개별 데이터 인사이트")
                query_parts.append("3. 실행 계획 포함")
                break
    
    # 분석 유형 기반 스타일
    if schema_analysis["potential_analyses"]:
        query_parts.append("\n🔍 **분석 유형별 스타일:**")
        if "시계열 분석" in str(schema_analysis["potential_analyses"]):
            query_parts.append("1. 트렌드 분석 중심")
            query_parts.append("2. 시계열 차트 포함")
        if "상관관계 분석" in str(schema_analysis["potential_analyses"]):
            query_parts.append("3. 상관관계 매트릭스")
            query_parts.append("4. 산점도 및 회귀분석")
        if "그룹별 성과 분석" in str(schema_analysis["potential_analyses"]):
            query_parts.append("5. 그룹별 비교 차트")
            query_parts.append("6. 성과 순위표")
    
    # 일반적인 스타일 옵션
    query_parts.append("\n📋 **일반 스타일 옵션:**")
    query_parts.append("7. 간단 요약만")
    query_parts.append("8. 인사이트 중심")
    query_parts.append("9. 예측 분석 포함")
    query_parts.append("10. 실행 계획 포함")
    
    query_parts.append("\n위 스타일 중에서 선택하거나, 원하는 스타일을 직접 설명해주세요.")
    
    return "\n".join(query_parts)


def _generate_report_format_query(user_responses: Dict[str, Any], 
                                schema_analysis: Dict[str, Any], 
                                summary_analysis: Dict[str, Any]) -> str:
    """5단계: 리포트 형식 질의 생성"""
    report_style = user_responses.get("report_style", "선택된 스타일")
    
    query_parts = [f"'{report_style}' 스타일의 리포트를 어떤 형식으로 받으시겠습니까?\n"]
    
    # 스타일 기반 형식 추천
    if "대시보드" in report_style or "시각화" in report_style:
        query_parts.append("📊 **시각화 중심 추천:**")
        query_parts.append("1. HTML (인터랙티브 대시보드)")
        query_parts.append("2. PowerPoint (프레젠테이션용)")
        query_parts.append("3. PDF (인쇄용)")
    
    if "상세 분석" in report_style or "데이터" in report_style:
        query_parts.append("\n📋 **데이터 분석 추천:**")
        query_parts.append("4. Excel (데이터 편집 가능)")
        query_parts.append("5. CSV (원시 데이터)")
        query_parts.append("6. JSON (구조화된 데이터)")
    
    if "요약" in report_style or "간단" in report_style:
        query_parts.append("\n📄 **문서형 추천:**")
        query_parts.append("7. PDF (공식 문서)")
        query_parts.append("8. Word (편집 가능)")
        query_parts.append("9. Markdown (개발자용)")
    
    # 일반적인 형식 옵션
    query_parts.append("\n📤 **전달 방식:**")
    query_parts.append("10. 이메일 전송")
    query_parts.append("11. 웹 대시보드")
    query_parts.append("12. 파일 다운로드")
    
    query_parts.append("\n위 형식 중에서 선택하거나, 다른 형식을 직접 입력해주세요.")
    
    return "\n".join(query_parts)


def _ask_report_type(user_responses: Dict[str, Any], data_schema: Dict[str, str], data_summary: Dict[str, Any]) -> QueryGenerationOutput:
    """1단계: 데이터 기반 리포트 유형을 동적으로 질의합니다."""
    query = _generate_dynamic_query(1, user_responses, data_schema, data_summary)
    return QueryGenerationOutput(
        next_query=query,
        current_step=1,
        next_step=2,
        collected_responses=user_responses
    )


def _ask_analysis_criteria(user_responses: Dict[str, Any], data_schema: Dict[str, str], data_summary: Dict[str, Any]) -> QueryGenerationOutput:
    """2단계: 데이터 기반 분석 기준을 동적으로 질의합니다."""
    query = _generate_dynamic_query(2, user_responses, data_schema, data_summary)
    return QueryGenerationOutput(
        next_query=query,
        current_step=2,
        next_step=3,
        collected_responses=user_responses
    )


def _ask_data_scope_and_filtering(user_responses: Dict[str, Any], data_schema: Dict[str, str], data_summary: Dict[str, Any]) -> QueryGenerationOutput:
    """3단계: 데이터 기반 범위 및 필터링 조건을 동적으로 질의합니다."""
    query = _generate_dynamic_query(3, user_responses, data_schema, data_summary)
    return QueryGenerationOutput(
        next_query=query,
        current_step=3,
        next_step=4,
        collected_responses=user_responses
    )


def _ask_report_style(user_responses: Dict[str, Any], data_schema: Dict[str, str], data_summary: Dict[str, Any]) -> QueryGenerationOutput:
    """4단계: 데이터 기반 리포트 스타일을 동적으로 질의합니다."""
    query = _generate_dynamic_query(4, user_responses, data_schema, data_summary)
    return QueryGenerationOutput(
        next_query=query,
        current_step=4,
        next_step=5,
        collected_responses=user_responses
    )


def _ask_report_format(user_responses: Dict[str, Any], data_schema: Dict[str, str], data_summary: Dict[str, Any]) -> QueryGenerationOutput:
    """5단계: 데이터 기반 리포트 파일 형식을 동적으로 질의합니다."""
    query = _generate_dynamic_query(5, user_responses, data_schema, data_summary)
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