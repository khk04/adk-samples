"""리포트 생성을 위한 동적 질의를 생성하는 도구"""

from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field
from google.adk.tools.function_tool import FunctionTool
import json
import re
import numpy as np
from datetime import datetime


class QueryGenerationInput(BaseModel):
    """리포트 생성을 위한 동적 질의 생성 입력"""
    current_step: int = Field(..., description="현재 질의 단계 (동적으로 결정 가능)")
    user_responses: Dict[str, Any] = Field(default_factory=dict, description="이전 단계에서 사용자의 응답")
    data_schema: Dict[str, str] = Field(default_factory=dict, description="분석할 데이터의 스키마 (컬럼명: 타입)")
    data_summary: Dict[str, Any] = Field(default_factory=dict, description="분석할 데이터의 요약 통계")
    user_input: Optional[str] = Field(None, description="사용자의 현재 단계 응답")
    conversation_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="대화 맥락 정보")


class QueryGenerationOutput(BaseModel):
    """동적 리포트 질의 생성 출력"""
    next_query: str = Field(..., description="사용자에게 던질 다음 질의")
    is_final_step: bool = Field(False, description="최종 단계 여부")
    report_guide: Optional[str] = Field(None, description="최종 리포트 생성 가이드 (최종 단계에서만 제공)")
    current_step: int = Field(..., description="현재 처리된 단계")
    next_step: Optional[int] = Field(None, description="다음 단계 번호 (None이면 완료)")
    collected_responses: Dict[str, Any] = Field(default_factory=dict, description="수집된 모든 사용자 응답")
    dynamic_insights: Optional[Dict[str, Any]] = Field(default_factory=dict, description="동적 분석 인사이트")
    suggested_questions: Optional[List[str]] = Field(default_factory=list, description="추가 제안 질의들")
    confidence_score: float = Field(default=0.0, description="질의 생성 신뢰도 (0-1)")


@FunctionTool
def generate_report_queries(
    current_step: int = 1, 
    user_responses: Dict[str, Any] = {}, 
    data_schema: Dict[str, str] = {}, 
    data_summary: Dict[str, Any] = {}, 
    user_input: Optional[str] = None,
    conversation_context: Optional[Dict[str, Any]] = None
) -> QueryGenerationOutput:
    """
    사용자 데이터 기반으로 최적의 리포트를 생성하기 위한 5단계 질의를 단계별로 처리합니다.
    데이터 특성과 사용자 응답 패턴을 분석하여 맞춤형 질의를 생성합니다.
    """
    if conversation_context is None:
        conversation_context = {}
    
    # 사용자 응답이 있으면 현재 단계에 저장
    if user_input is not None:
        step_key = _get_step_key(current_step)
        user_responses[step_key] = user_input
    
    # 5단계 질의 생성 수행
    return _generate_5step_queries(
        current_step, user_responses, data_schema, data_summary, conversation_context
        )


def _get_step_key(step: int) -> str:
    """단계 번호에 따른 응답 키를 반환합니다."""
    step_keys = {
        1: "domain_identification",
        2: "analysis_scope", 
        3: "data_filtering",
        4: "report_style",
        5: "output_format"
    }
    return step_keys.get(step, f"step_{step}")


def _get_5step_definitions() -> List[Dict[str, Any]]:
    """5단계 질의 정의를 반환합니다."""
    return [
        {
            "type": "domain_identification",
            "title": "도메인 식별 및 리포트 유형 확인",
            "description": "데이터를 분석하여 비즈니스 도메인을 식별하고 리포트 유형을 확인합니다.",
            "priority": 1,
            "required": True
        },
        {
            "type": "analysis_scope",
            "title": "분석 범위 및 기준 설정",
            "description": "도메인별 특화 분석 범위와 기준을 설정합니다.",
            "priority": 2,
            "required": True
        },
        {
            "type": "data_filtering",
            "title": "데이터 범위 및 필터링 조건 정의",
            "description": "데이터 크기와 복잡도에 따른 최적 필터링 전략을 설정합니다.",
            "priority": 3,
            "required": True
        },
        {
            "type": "report_style",
            "title": "리포트 스타일 및 상세 수준 결정",
            "description": "사용자의 기술 수준과 상세도 선호에 따른 리포트 스타일을 결정합니다.",
            "priority": 4,
            "required": True
        },
        {
            "type": "output_format",
            "title": "리포트 파일 형식 및 전달 방식 확인",
            "description": "사용자의 기술 수준과 선호도에 따른 출력 형식을 결정합니다.",
            "priority": 5,
            "required": True
        }
    ]


def _generate_5step_queries(
    current_step: int, 
    user_responses: Dict[str, Any], 
    data_schema: Dict[str, str], 
    data_summary: Dict[str, Any],
    conversation_context: Dict[str, Any]
) -> QueryGenerationOutput:
    """5단계 질의 생성 메인 함수"""
    
    # 고급 데이터 분석 수행
    advanced_analysis = _perform_advanced_data_analysis(data_schema, data_summary)
    
    # 도메인 식별
    domain_info = _identify_business_domain(data_schema, data_summary, user_responses)
    
    # 사용자 응답 패턴 분석
    response_pattern = _analyze_user_response_pattern(user_responses, conversation_context)
    
    # 5단계 질의 정의
    step_definitions = _get_5step_definitions()
    
    # 현재 단계에 맞는 질의 생성
    if current_step <= 5:
        step_info = step_definitions[current_step - 1]
        query_result = _generate_contextual_query(
            current_step, step_info, user_responses, advanced_analysis, domain_info, response_pattern
        )
        
        # 신뢰도 계산
        confidence = _calculate_confidence_score(advanced_analysis, domain_info, response_pattern)
        
        # 추가 제안 질의 생성
        suggested_questions = _generate_suggested_questions(advanced_analysis, domain_info, current_step)
        
        return QueryGenerationOutput(
            next_query=query_result["query"],
            current_step=current_step,
            next_step=current_step + 1 if current_step < 5 else None,
            is_final_step=current_step >= 5,
            report_guide=query_result.get("report_guide"),
            collected_responses=user_responses,
            dynamic_insights={
                "domain": domain_info,
                "analysis": advanced_analysis,
                "pattern": response_pattern,
                "steps": step_definitions
            },
            suggested_questions=suggested_questions,
            confidence_score=confidence
        )
    else:
        # 모든 단계 완료
        return QueryGenerationOutput(
            next_query="모든 질의 단계가 완료되었습니다. 수집된 정보를 바탕으로 리포트를 생성할 준비가 되었습니다. 리포트 생성을 진행하시겠습니까? (예/아니요)",
            is_final_step=True,
            report_guide=_generate_advanced_report_guide(user_responses, advanced_analysis, domain_info),
            current_step=current_step,
            collected_responses=user_responses,
            dynamic_insights={
                "domain": domain_info,
                "analysis": advanced_analysis,
                "pattern": response_pattern
            },
            confidence_score=0.9
        )




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


def _perform_advanced_data_analysis(data_schema: Dict[str, str], data_summary: Dict[str, Any]) -> Dict[str, Any]:
    """고급 데이터 분석을 수행하여 더 정교한 인사이트를 도출합니다."""
    analysis = {
        "data_complexity": _calculate_data_complexity(data_schema, data_summary),
        "business_indicators": _identify_business_indicators(data_schema),
        "analytical_potential": _assess_analytical_potential(data_schema, data_summary),
        "data_quality_score": _calculate_data_quality_score(data_summary),
        "temporal_patterns": _detect_temporal_patterns(data_schema),
        "categorical_richness": _assess_categorical_richness(data_schema, data_summary),
        "numerical_distribution": _analyze_numerical_distribution(data_schema, data_summary),
        "correlation_potential": _assess_correlation_potential(data_schema),
        "anomaly_detection_potential": _assess_anomaly_detection_potential(data_schema, data_summary)
    }
    return analysis


def _identify_business_domain(data_schema: Dict[str, str], data_summary: Dict[str, Any], user_responses: Dict[str, Any]) -> Dict[str, Any]:
    """비즈니스 도메인을 식별하고 도메인별 특화 정보를 제공합니다."""
    domain_indicators = {
        "ecommerce": ["product", "order", "customer", "price", "cart", "payment", "shipping"],
        "finance": ["account", "transaction", "balance", "credit", "debit", "loan", "investment"],
        "healthcare": ["patient", "diagnosis", "treatment", "medical", "hospital", "doctor", "prescription"],
        "education": ["student", "course", "grade", "teacher", "school", "exam", "curriculum"],
        "marketing": ["campaign", "lead", "conversion", "click", "impression", "engagement", "roi"],
        "hr": ["employee", "salary", "department", "performance", "attendance", "recruitment"],
        "logistics": ["shipment", "warehouse", "inventory", "delivery", "supplier", "route"],
        "real_estate": ["property", "rent", "lease", "building", "location", "price", "area"],
        "manufacturing": ["production", "quality", "machine", "defect", "efficiency", "capacity"],
        "retail": ["store", "sales", "inventory", "customer", "product", "revenue"]
    }
    
    column_names = [col.lower() for col in data_schema.keys()]
    domain_scores = {}
    
    for domain, keywords in domain_indicators.items():
        score = 0
        matched_keywords = []
        for keyword in keywords:
            for col in column_names:
                if keyword in col:
                    score += 1
                    matched_keywords.append(keyword)
        domain_scores[domain] = {
            "score": score,
            "matched_keywords": matched_keywords,
            "confidence": min(score / len(keywords), 1.0)
        }
    
    # 가장 높은 점수의 도메인 선택
    best_domain = max(domain_scores.items(), key=lambda x: x[1]["score"])
    
    return {
        "primary_domain": best_domain[0] if best_domain[1]["score"] > 0 else "general",
        "domain_scores": domain_scores,
        "domain_confidence": best_domain[1]["confidence"],
        "domain_specific_insights": _get_domain_specific_insights(best_domain[0], data_schema, data_summary)
    }


def _analyze_user_response_pattern(user_responses: Dict[str, Any], conversation_context: Dict[str, Any]) -> Dict[str, Any]:
    """사용자 응답 패턴을 분석하여 질의 개선에 활용합니다."""
    pattern = {
        "response_length": _analyze_response_length(user_responses),
        "preference_style": _analyze_preference_style(user_responses),
        "technical_level": _assess_technical_level(user_responses),
        "detail_preference": _assess_detail_preference(user_responses),
        "interaction_style": _analyze_interaction_style(conversation_context),
        "decision_making_style": _analyze_decision_making_style(user_responses)
    }
    return pattern


def _determine_dynamic_steps(advanced_analysis: Dict[str, Any], domain_info: Dict[str, Any], response_pattern: Dict[str, Any]) -> List[Dict[str, Any]]:
    """데이터 특성과 사용자 패턴을 기반으로 동적 단계를 결정합니다."""
    steps = []
    
    # 기본 단계들
    base_steps = [
        {"type": "domain_identification", "priority": 1, "required": True},
        {"type": "analysis_scope", "priority": 2, "required": True},
        {"type": "data_filtering", "priority": 3, "required": True},
        {"type": "report_style", "priority": 4, "required": True},
        {"type": "output_format", "priority": 5, "required": True}
    ]
    
    # 도메인별 특화 단계 추가
    domain = domain_info.get("primary_domain", "general")
    if domain == "ecommerce":
        steps.append({"type": "customer_segmentation", "priority": 2.5, "required": False})
        steps.append({"type": "product_analysis", "priority": 3.5, "required": False})
    elif domain == "finance":
        steps.append({"type": "risk_assessment", "priority": 2.5, "required": False})
        steps.append({"type": "compliance_check", "priority": 3.5, "required": False})
    elif domain == "marketing":
        steps.append({"type": "campaign_effectiveness", "priority": 2.5, "required": False})
        steps.append({"type": "audience_analysis", "priority": 3.5, "required": False})
    
    # 데이터 복잡도에 따른 단계 추가
    complexity = advanced_analysis.get("data_complexity", "medium")
    if complexity == "high":
        steps.append({"type": "data_quality_assessment", "priority": 1.5, "required": True})
        steps.append({"type": "advanced_analytics", "priority": 4.5, "required": False})
    
    # 사용자 선호도에 따른 단계 조정
    if response_pattern.get("detail_preference") == "high":
        steps.append({"type": "detailed_breakdown", "priority": 4.5, "required": False})
    
    # 모든 단계를 우선순위로 정렬
    all_steps = base_steps + steps
    all_steps.sort(key=lambda x: x["priority"])
    
    return all_steps


def _generate_contextual_query(
    current_step: int, 
    step_info: Dict[str, Any], 
    user_responses: Dict[str, Any], 
    advanced_analysis: Dict[str, Any], 
    domain_info: Dict[str, Any], 
    response_pattern: Dict[str, Any]
) -> Dict[str, Any]:
    """LLM을 활용하여 컨텍스트를 고려한 완전히 동적인 질의를 생성합니다."""
    
    step_type = step_info["type"]
    domain = domain_info.get("primary_domain", "general")
    
    # LLM 기반 동적 질의 생성
    return _generate_llm_dynamic_query(
        step_type, current_step, user_responses, advanced_analysis, domain_info, response_pattern
    )


def _generate_llm_dynamic_query(
    step_type: str,
    current_step: int,
    user_responses: Dict[str, Any],
    advanced_analysis: Dict[str, Any],
    domain_info: Dict[str, Any],
    response_pattern: Dict[str, Any]
) -> Dict[str, Any]:
    """
    LLM을 활용하여 완전히 동적인 질의를 생성합니다.
    이 함수는 에이전트의 LLM 능력을 활용하여 데이터와 사용자 패턴을 분석하여
    맞춤형 질의를 생성합니다.
    """
    
    # LLM에게 전달할 컨텍스트 정보 구성
    context_info = {
        "step_type": step_type,
        "current_step": current_step,
        "domain": domain_info.get("primary_domain", "general"),
        "domain_confidence": domain_info.get("domain_confidence", 0.0),
        "data_complexity": advanced_analysis.get("data_complexity", "medium"),
        "data_quality_score": advanced_analysis.get("data_quality_score", 0.5),
        "user_response_pattern": response_pattern,
        "previous_responses": user_responses,
        "business_indicators": advanced_analysis.get("business_indicators", {}),
        "analytical_potential": advanced_analysis.get("analytical_potential", {}),
        "domain_insights": domain_info.get("domain_specific_insights", {})
    }
    
    # LLM 기반 동적 질의 생성 프롬프트
    llm_prompt = f"""
당신은 데이터 분석 전문가입니다. 다음 정보를 바탕으로 사용자에게 던질 맞춤형 질의를 생성해주세요.

**현재 상황:**
- 단계: {step_type} (전체 {current_step}단계 중)
- 식별된 도메인: {context_info['domain']} (신뢰도: {context_info['domain_confidence']:.2f})
- 데이터 복잡도: {context_info['data_complexity']}
- 데이터 품질 점수: {context_info['data_quality_score']:.2f}

**사용자 패턴 분석:**
- 응답 길이: {response_pattern.get('response_length', 'unknown')}
- 선호 스타일: {response_pattern.get('preference_style', 'unknown')}
- 기술 수준: {response_pattern.get('technical_level', 'unknown')}
- 상세도 선호: {response_pattern.get('detail_preference', 'medium')}
- 의사결정 스타일: {response_pattern.get('decision_making_style', 'unknown')}

**이전 사용자 응답:**
{json.dumps(user_responses, ensure_ascii=False, indent=2)}

**데이터 분석 결과:**
- 비즈니스 지표: {context_info['business_indicators']}
- 분석 잠재력: {context_info['analytical_potential']}
- 도메인별 인사이트: {context_info['domain_insights']}

**요구사항:**
1. 위 정보를 종합 분석하여 사용자에게 맞춤형 질의를 생성하세요
2. 질의는 사용자의 기술 수준과 선호도에 맞춰 조정하세요
3. 도메인별 특화된 내용을 포함하세요
4. 구체적이고 실행 가능한 선택지를 제공하세요
5. 사용자의 이전 응답 패턴을 고려하여 일관성 있게 작성하세요

**출력 형식:**
- 질의 내용 (사용자에게 보여줄 질문)
- 선택지들 (번호가 매겨진 구체적인 옵션들)
- 추가 설명 (필요시)

질의를 생성해주세요:
"""
    
    # LLM 기반 질의 생성 (에이전트가 이 프롬프트를 처리)
    # 실제로는 에이전트의 LLM이 이 프롬프트를 받아서 동적으로 질의를 생성
    dynamic_query = _simulate_llm_query_generation(llm_prompt, context_info)
    
    return {"query": dynamic_query}


def _simulate_llm_query_generation(llm_prompt: str, context_info: Dict[str, Any]) -> str:
    """
    LLM 기반 질의 생성을 시뮬레이션합니다.
    실제로는 에이전트의 LLM이 이 함수를 호출하여 동적으로 질의를 생성합니다.
    """
    
    step_type = context_info["step_type"]
    domain = context_info["domain"]
    user_pattern = context_info["user_response_pattern"]
    domain_insights = context_info["domain_insights"]
    
    # LLM이 생성할 동적 질의의 예시 (실제로는 LLM이 생성)
    if step_type == "domain_identification":
        if context_info["domain_confidence"] > 0.7:
            return f"""데이터를 분석한 결과, '{domain}' 도메인으로 판단됩니다 (신뢰도: {context_info['domain_confidence']:.1%}).

{domain_insights.get('key_metrics', [])} 등의 핵심 지표가 발견되었습니다.

이 분석이 맞다면 계속 진행하시겠습니까, 아니면 다른 도메인을 선택하시겠습니까?

1. 네, {domain} 도메인으로 계속 진행
2. 다른 도메인 선택하기
3. 도메인 분석 결과 자세히 보기"""
        else:
            return f"""데이터를 분석한 결과, 여러 도메인이 가능해 보입니다.

현재 가장 가능성이 높은 도메인: {domain} (신뢰도: {context_info['domain_confidence']:.1%})

어떤 도메인에 해당하는지 선택해주세요:

1. {domain} 도메인
2. 다른 도메인 직접 입력
3. 도메인 분석 결과 자세히 보기"""

    elif step_type == "analysis_scope":
        technical_level = user_pattern.get("technical_level", "medium")
        detail_preference = user_pattern.get("detail_preference", "medium")
        
        if technical_level == "high" and detail_preference == "high":
            return f"""'{domain}' 도메인에 대한 상세한 분석을 진행하겠습니다.

고급 분석 옵션들:
1. 통계적 모델링 및 예측 분석
2. 머신러닝 기반 패턴 탐지
3. 다변량 분석 및 상관관계 분석
4. 시계열 분석 및 트렌드 예측
5. 클러스터링 및 세분화 분석
6. 맞춤형 분석 요청

어떤 분석을 원하시나요?"""
        else:
            return f"""'{domain}' 도메인 분석을 위한 범위를 선택해주세요.

추천 분석:
1. 핵심 지표 분석
2. 트렌드 분석
3. 비교 분석
4. 인사이트 도출
5. 맞춤형 분석

어떤 분석을 원하시나요?"""

    elif step_type == "data_filtering":
        complexity = context_info["data_complexity"]
        quality_score = context_info["data_quality_score"]
        
        if complexity == "high":
            return f"""대용량 데이터({context_info.get('total_rows', 'N/A')}행) 분석을 위한 필터링 전략을 선택해주세요.

성능 최적화 옵션:
1. 최근 데이터 샘플링 (최근 3개월)
2. 상위 성과 데이터 (상위 20%)
3. 계층적 샘플링 (대표성 보장)
4. 특정 조건 필터링
5. 전체 데이터 분석 (시간 소요)

데이터 품질 점수: {quality_score:.1%}
어떤 방식을 선택하시겠습니까?"""
        else:
            return f"""데이터 필터링 조건을 선택해주세요.

분석 범위:
1. 전체 데이터
2. 특정 기간
3. 조건별 필터링
4. 샘플링 분석

데이터 품질: {quality_score:.1%}
어떤 범위로 분석하시겠습니까?"""

    elif step_type == "report_style":
        detail_pref = user_pattern.get("detail_preference", "medium")
        tech_level = user_pattern.get("technical_level", "medium")
        
        if detail_pref == "high":
            return f"""상세한 분석을 원하시는군요! 리포트 스타일을 선택해주세요.

상세 분석 옵션:
1. 포괄적 상세 분석 (모든 데이터 포함)
2. 단계별 상세 설명 (분석 과정 포함)
3. 데이터 원본 및 중간 결과 포함
4. 통계적 유의성 검정 포함
5. 맞춤형 상세 분석

어떤 스타일을 원하시나요?"""
        elif detail_pref == "low":
            return f"""핵심만 간단히 원하시는군요! 리포트 스타일을 선택해주세요.

간단 요약 옵션:
1. 핵심 인사이트만 (3-5개)
2. 실행 계획 중심
3. 대시보드 스타일
4. 한 페이지 요약
5. 맞춤형 간단 분석

어떤 스타일을 원하시나요?"""
        else:
            return f"""균형잡힌 분석을 원하시는군요! 리포트 스타일을 선택해주세요.

균형 분석 옵션:
1. 요약 + 상세 분석
2. 인사이트 + 실행 방안
3. 시각화 포함
4. 비교 분석 포함
5. 맞춤형 균형 분석

어떤 스타일을 원하시나요?"""

    elif step_type == "output_format":
        tech_level = user_pattern.get("technical_level", "medium")
        
        if tech_level == "high":
            return f"""기술적 수준이 높으시니 다양한 형식을 제공하겠습니다.

출력 형식 선택:
1. PDF (공식 문서)
2. HTML (인터랙티브 대시보드)
3. Excel (데이터 편집 가능)
4. JSON (구조화된 데이터)
5. CSV (원시 데이터)
6. Markdown (개발자용)
7. 맞춤형 형식

어떤 형식을 원하시나요?"""
        else:
            return f"""리포트 출력 형식을 선택해주세요.

출력 형식:
1. PDF (공식 문서)
2. HTML (웹 브라우저)
3. PowerPoint (프레젠테이션)
4. Word (편집 가능)
5. 맞춤형 형식

어떤 형식을 원하시나요?"""

    else:
        # 도메인별 특화 질의
        return f"""{step_type} 관련 추가 분석을 원하시나요?

{domain} 도메인 특화 옵션:
1. 도메인별 핵심 분석
2. 특화 지표 분석
3. 업계 벤치마크 비교
4. 맞춤형 분석
5. 건너뛰기

어떤 분석을 원하시나요?"""


def _calculate_confidence_score(advanced_analysis: Dict[str, Any], domain_info: Dict[str, Any], response_pattern: Dict[str, Any]) -> float:
    """질의 생성의 신뢰도를 계산합니다."""
    confidence_factors = []
    
    # 도메인 식별 신뢰도
    domain_confidence = domain_info.get("domain_confidence", 0.0)
    confidence_factors.append(domain_confidence * 0.3)
    
    # 데이터 품질 점수
    data_quality = advanced_analysis.get("data_quality_score", 0.0)
    confidence_factors.append(data_quality * 0.2)
    
    # 사용자 응답 패턴 일관성
    response_consistency = _calculate_response_consistency(response_pattern)
    confidence_factors.append(response_consistency * 0.2)
    
    # 데이터 복잡도 적절성
    complexity_score = _calculate_complexity_score(advanced_analysis)
    confidence_factors.append(complexity_score * 0.3)
    
    return min(sum(confidence_factors), 1.0)


def _generate_suggested_questions(advanced_analysis: Dict[str, Any], domain_info: Dict[str, Any], current_step: int) -> List[str]:
    """추가 제안 질의들을 생성합니다."""
    suggestions = []
    domain = domain_info.get("primary_domain", "general")
    
    # 도메인별 제안 질의
    if domain == "ecommerce":
        suggestions.extend([
            "고객 세분화 분석을 원하시나요?",
            "제품별 성과 비교 분석을 포함하시겠습니까?",
            "계절성 트렌드 분석을 추가하시겠습니까?"
        ])
    elif domain == "finance":
        suggestions.extend([
            "리스크 분석을 포함하시겠습니까?",
            "수익성 분석을 추가하시겠습니까?",
            "규정 준수 체크를 포함하시겠습니까?"
        ])
    
    # 데이터 특성 기반 제안
    if advanced_analysis.get("temporal_patterns", {}).get("has_time_series"):
        suggestions.append("시계열 분석을 포함하시겠습니까?")
    
    if advanced_analysis.get("correlation_potential", {}).get("high_correlation_count", 0) > 0:
        suggestions.append("상관관계 분석을 추가하시겠습니까?")
    
    return suggestions[:3]  # 최대 3개 제안


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






# ===== 고급 분석 헬퍼 함수들 =====

def _calculate_data_complexity(data_schema: Dict[str, str], data_summary: Dict[str, Any]) -> str:
    """데이터 복잡도를 계산합니다."""
    total_columns = len(data_schema)
    total_rows = data_summary.get("total_rows", 0)
    
    if total_columns > 20 or total_rows > 100000:
        return "high"
    elif total_columns > 10 or total_rows > 10000:
        return "medium"
    else:
        return "low"


def _identify_business_indicators(data_schema: Dict[str, str]) -> Dict[str, Any]:
    """비즈니스 지표를 식별합니다."""
    indicators = {
        "financial": [],
        "operational": [],
        "customer": [],
        "product": []
    }
    
    for col in data_schema.keys():
        col_lower = col.lower()
        if any(word in col_lower for word in ["revenue", "profit", "cost", "price", "amount"]):
            indicators["financial"].append(col)
        elif any(word in col_lower for word in ["efficiency", "performance", "quality", "time"]):
            indicators["operational"].append(col)
        elif any(word in col_lower for word in ["customer", "client", "user", "satisfaction"]):
            indicators["customer"].append(col)
        elif any(word in col_lower for word in ["product", "item", "category", "inventory"]):
            indicators["product"].append(col)
    
    return indicators


def _assess_analytical_potential(data_schema: Dict[str, str], data_summary: Dict[str, Any]) -> Dict[str, Any]:
    """분석 잠재력을 평가합니다."""
    potential = {
        "statistical_analysis": False,
        "time_series_analysis": False,
        "correlation_analysis": False,
        "clustering_analysis": False,
        "predictive_analysis": False
    }
    
    # 수치형 컬럼이 2개 이상이면 상관관계 분석 가능
    numeric_cols = [col for col, dtype in data_schema.items() if dtype in ['int64', 'float64', 'int32', 'float32']]
    if len(numeric_cols) >= 2:
        potential["correlation_analysis"] = True
        potential["statistical_analysis"] = True
    
    # 날짜 컬럼이 있으면 시계열 분석 가능
    date_cols = [col for col, dtype in data_schema.items() 
                 if (isinstance(dtype, str) and 'date' in dtype.lower()) or 'time' in col.lower()]
    if date_cols:
        potential["time_series_analysis"] = True
        potential["predictive_analysis"] = True
    
    # 범주형 컬럼이 있으면 클러스터링 분석 가능
    categorical_cols = [col for col, dtype in data_schema.items() if dtype in ['object', 'category']]
    if len(categorical_cols) >= 2:
        potential["clustering_analysis"] = True
    
    return potential


def _calculate_data_quality_score(data_summary: Dict[str, Any]) -> float:
    """데이터 품질 점수를 계산합니다."""
    if not data_summary:
        return 0.5
    
    score = 1.0
    
    # 결측값 비율에 따른 점수 조정
    missing_values = data_summary.get("missing_values", {})
    if missing_values:
        # missing_values가 dict인지 확인
        if isinstance(missing_values, dict):
            # missing_values의 값들이 정수와 문자열이 섞여있을 수 있으므로 안전하게 처리
            total_missing = 0
            for value in missing_values.values():
                if isinstance(value, (int, float)):
                    total_missing += value
                elif isinstance(value, str) and value.isdigit():
                    total_missing += int(value)
            
            total_cells = data_summary.get("total_rows", 1) * len(missing_values)
            missing_ratio = total_missing / total_cells if total_cells > 0 else 0
            score -= missing_ratio * 0.5
        elif isinstance(missing_values, (int, float)):
            # missing_values가 단일 숫자인 경우
            total_cells = data_summary.get("total_rows", 1)
            missing_ratio = missing_values / total_cells if total_cells > 0 else 0
            score -= missing_ratio * 0.5
    
    return max(score, 0.0)


def _detect_temporal_patterns(data_schema: Dict[str, str]) -> Dict[str, Any]:
    """시간적 패턴을 감지합니다."""
    patterns = {
        "has_time_series": False,
        "date_columns": [],
        "time_granularity": "unknown"
    }
    
    for col, dtype in data_schema.items():
        if (isinstance(dtype, str) and 'date' in dtype.lower()) or 'time' in col.lower():
            patterns["date_columns"].append(col)
            patterns["has_time_series"] = True
    
    return patterns


def _assess_categorical_richness(data_schema: Dict[str, str], data_summary: Dict[str, Any]) -> Dict[str, Any]:
    """범주형 데이터의 풍부함을 평가합니다."""
    richness = {
        "high_diversity_columns": [],
        "low_diversity_columns": [],
        "richness_score": 0.0
    }
    
    categorical_stats = data_summary.get("categorical_stats", {})
    for col, stats in categorical_stats.items():
        unique_count = stats.get("unique_count", 0)
        total_rows = data_summary.get("total_rows", 1)
        diversity_ratio = unique_count / total_rows
        
        if diversity_ratio > 0.5:
            richness["high_diversity_columns"].append(col)
        elif diversity_ratio < 0.1:
            richness["low_diversity_columns"].append(col)
    
    richness["richness_score"] = len(richness["high_diversity_columns"]) / max(len(categorical_stats), 1)
    return richness


def _analyze_numerical_distribution(data_schema: Dict[str, str], data_summary: Dict[str, Any]) -> Dict[str, Any]:
    """수치형 데이터의 분포를 분석합니다."""
    distribution = {
        "normal_distributions": [],
        "skewed_distributions": [],
        "uniform_distributions": []
    }
    
    numeric_stats = data_summary.get("numeric_stats", {})
    for col, stats in numeric_stats.items():
        if "std" in stats and "mean" in stats:
            cv = stats["std"] / stats["mean"] if stats["mean"] != 0 else 0
            if 0.3 <= cv <= 0.7:
                distribution["normal_distributions"].append(col)
            elif cv > 1.0:
                distribution["skewed_distributions"].append(col)
            elif cv < 0.3:
                distribution["uniform_distributions"].append(col)
    
    return distribution


def _assess_correlation_potential(data_schema: Dict[str, str]) -> Dict[str, Any]:
    """상관관계 분석 잠재력을 평가합니다."""
    numeric_cols = [col for col, dtype in data_schema.items() if dtype in ['int64', 'float64', 'int32', 'float32']]
    
    return {
        "high_correlation_count": len(numeric_cols),
        "correlation_pairs": len(numeric_cols) * (len(numeric_cols) - 1) // 2 if len(numeric_cols) > 1 else 0,
        "analysis_feasible": len(numeric_cols) >= 2
    }


def _assess_anomaly_detection_potential(data_schema: Dict[str, str], data_summary: Dict[str, Any]) -> Dict[str, Any]:
    """이상치 탐지 잠재력을 평가합니다."""
    numeric_cols = [col for col, dtype in data_schema.items() if dtype in ['int64', 'float64', 'int32', 'float32']]
    total_rows = data_summary.get("total_rows", 0)
    
    return {
        "feasible": len(numeric_cols) > 0 and total_rows > 100,
        "recommended_methods": ["iqr", "z_score"] if len(numeric_cols) > 0 else [],
        "data_size_adequate": total_rows > 1000
    }


def _get_domain_specific_insights(domain: str, data_schema: Dict[str, str], data_summary: Dict[str, Any]) -> Dict[str, Any]:
    """도메인별 특화 인사이트를 제공합니다."""
    insights = {
        "key_metrics": [],
        "recommended_analyses": [],
        "business_questions": []
    }
    
    if domain == "ecommerce":
        insights["key_metrics"] = ["고객 생애 가치", "전환율", "평균 주문 가치"]
        insights["recommended_analyses"] = ["고객 세분화", "제품 성과 분석", "계절성 트렌드"]
        insights["business_questions"] = ["어떤 제품이 가장 수익성이 높은가?", "고객 유지율은 어떻게 되는가?"]
    elif domain == "finance":
        insights["key_metrics"] = ["수익률", "리스크 지표", "유동성 비율"]
        insights["recommended_analyses"] = ["포트폴리오 분석", "리스크 평가", "수익성 분석"]
        insights["business_questions"] = ["투자 수익률은 어떻게 되는가?", "리스크는 어느 정도인가?"]
    
    return insights


def _analyze_response_length(user_responses: Dict[str, Any]) -> str:
    """사용자 응답 길이를 분석합니다."""
    if not user_responses:
        return "unknown"
    
    avg_length = sum(len(str(response)) for response in user_responses.values()) / len(user_responses)
    
    if avg_length > 50:
        return "detailed"
    elif avg_length > 20:
        return "moderate"
    else:
        return "brief"


def _analyze_preference_style(user_responses: Dict[str, Any]) -> str:
    """사용자 선호 스타일을 분석합니다."""
    if not user_responses:
        return "unknown"
    
    responses_text = " ".join(str(response) for response in user_responses.values()).lower()
    
    if any(word in responses_text for word in ["상세", "자세", "구체", "세부"]):
        return "detailed"
    elif any(word in responses_text for word in ["간단", "요약", "핵심", "간략"]):
        return "summary"
    else:
        return "balanced"


def _assess_technical_level(user_responses: Dict[str, Any]) -> str:
    """사용자의 기술적 수준을 평가합니다."""
    if not user_responses:
        return "unknown"
    
    responses_text = " ".join(str(response) for response in user_responses.values()).lower()
    
    technical_terms = ["분석", "통계", "모델", "알고리즘", "데이터", "인사이트"]
    technical_count = sum(1 for term in technical_terms if term in responses_text)
    
    if technical_count >= 3:
        return "high"
    elif technical_count >= 1:
        return "medium"
    else:
        return "low"


def _assess_detail_preference(user_responses: Dict[str, Any]) -> str:
    """사용자의 상세도 선호를 평가합니다."""
    if not user_responses:
        return "medium"
    
    responses_text = " ".join(str(response) for response in user_responses.values()).lower()
    
    if any(word in responses_text for word in ["상세", "자세", "구체", "세부", "모든"]):
        return "high"
    elif any(word in responses_text for word in ["간단", "요약", "핵심", "간략", "주요"]):
        return "low"
    else:
        return "medium"


def _analyze_interaction_style(conversation_context: Dict[str, Any]) -> str:
    """사용자의 상호작용 스타일을 분석합니다."""
    if not conversation_context:
        return "unknown"
    
    # 대화 맥락에서 스타일 추론
    return "collaborative"  # 기본값


def _analyze_decision_making_style(user_responses: Dict[str, Any]) -> str:
    """사용자의 의사결정 스타일을 분석합니다."""
    if not user_responses:
        return "unknown"
    
    responses_text = " ".join(str(response) for response in user_responses.values()).lower()
    
    if any(word in responses_text for word in ["빠르", "신속", "즉시", "바로"]):
        return "quick"
    elif any(word in responses_text for word in ["신중", "검토", "고려", "분석"]):
        return "deliberate"
    else:
        return "balanced"


def _calculate_response_consistency(response_pattern: Dict[str, Any]) -> float:
    """사용자 응답의 일관성을 계산합니다."""
    # 간단한 일관성 점수 계산
    consistency_factors = []
    
    if response_pattern.get("response_length") != "unknown":
        consistency_factors.append(0.3)
    if response_pattern.get("preference_style") != "unknown":
        consistency_factors.append(0.3)
    if response_pattern.get("technical_level") != "unknown":
        consistency_factors.append(0.4)
    
    return sum(consistency_factors) / len(consistency_factors) if consistency_factors else 0.5


def _calculate_complexity_score(advanced_analysis: Dict[str, Any]) -> float:
    """데이터 복잡도 적절성 점수를 계산합니다."""
    complexity = advanced_analysis.get("data_complexity", "medium")
    quality_score = advanced_analysis.get("data_quality_score", 0.5)
    
    if complexity == "high" and quality_score > 0.7:
        return 0.9
    elif complexity == "medium" and quality_score > 0.5:
        return 0.8
    elif complexity == "low":
        return 0.7
    else:
        return 0.5




def _generate_advanced_report_guide(user_responses: Dict[str, Any], advanced_analysis: Dict[str, Any], domain_info: Dict[str, Any]) -> str:
    """고급 리포트 생성 가이드를 생성합니다."""
    domain = domain_info.get("primary_domain", "general")
    insights = domain_info.get("domain_specific_insights", {})

    guide = f"""
    ---
**고급 리포트 생성 가이드:**

**식별된 도메인:** {domain}
**도메인 신뢰도:** {domain_info.get('domain_confidence', 0.0):.2f}
**데이터 품질 점수:** {advanced_analysis.get('data_quality_score', 0.0):.2f}

**수집된 사용자 응답:**
"""
    
    for key, value in user_responses.items():
        guide += f"- {key}: {value}\n"
    
    if insights.get("key_metrics"):
        guide += f"\n**도메인별 핵심 지표:** {', '.join(insights['key_metrics'])}"
    
    if insights.get("recommended_analyses"):
        guide += f"\n**추천 분석:** {', '.join(insights['recommended_analyses'])}"
    
    guide += "\n\n위 정보를 바탕으로 맞춤형 리포트를 생성할 준비가 되었습니다."
    guide += "\n---"
    
    return guide


class QueryGenerationTool:
    def __init__(self):
        self.name = "generate_report_queries"
        self.description = "사용자 데이터 기반으로 최적의 리포트를 생성하기 위한 동적 질의를 자동 생성합니다."
        self.input_model = QueryGenerationInput
        self.output_model = QueryGenerationOutput
        self.execute = generate_report_queries