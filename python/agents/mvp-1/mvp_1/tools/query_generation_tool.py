"""리포트 생성을 위한 질의 생성 컨텍스트를 제공하는 도구"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from google.adk.tools.function_tool import FunctionTool


class QueryGenerationInput(BaseModel):
    """질의 생성 컨텍스트 제공 입력"""
    current_step: int = Field(..., description="현재 질의 단계 (1-5)")
    user_responses: Dict[str, Any] = Field(default_factory=dict, description="이전 단계에서 사용자의 응답")
    data_schema: Dict[str, str] = Field(default_factory=dict, description="분석할 데이터의 스키마 (컬럼명: 타입)")
    data_summary: Dict[str, Any] = Field(default_factory=dict, description="분석할 데이터의 요약 통계")
    user_input: Optional[str] = Field(None, description="사용자의 현재 단계 응답")
    conversation_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="대화 맥락 정보")


class QueryGenerationOutput(BaseModel):
    """질의 생성 컨텍스트 출력"""
    current_step: int = Field(..., description="현재 처리된 단계")
    next_step: Optional[int] = Field(None, description="다음 단계 번호 (None이면 완료)")
    is_final_step: bool = Field(False, description="최종 단계 여부")
    collected_responses: Dict[str, Any] = Field(default_factory=dict, description="수집된 모든 사용자 응답")
    analysis_context: Dict[str, Any] = Field(default_factory=dict, description="질의 생성을 위한 분석 컨텍스트")
    step_guidance: str = Field(..., description="현재 단계에 대한 질의 생성 가이드")


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
    질의 생성을 위한 컨텍스트 정보를 제공합니다.
    에이전트가 이 정보를 바탕으로 동적으로 질의를 생성합니다.
    """
    if conversation_context is None:
        conversation_context = {}
    
    # 사용자 응답이 있으면 현재 단계에 저장
    if user_input is not None:
        step_key = _get_step_key(current_step)
        user_responses[step_key] = user_input
    
    # 분석 컨텍스트 생성
    analysis_context = _generate_analysis_context(data_schema, data_summary, user_responses)
    
    # 현재 단계 가이드 생성
    step_guidance = _generate_step_guidance(current_step, analysis_context)
    
    return QueryGenerationOutput(
        current_step=current_step,
        next_step=current_step + 1 if current_step < 5 else None,
        is_final_step=current_step >= 5,
        collected_responses=user_responses,
        analysis_context=analysis_context,
        step_guidance=step_guidance
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


def _generate_analysis_context(data_schema: Dict[str, str], data_summary: Dict[str, Any], user_responses: Dict[str, Any]) -> Dict[str, Any]:
    """질의 생성을 위한 분석 컨텍스트를 생성합니다."""
    return {
        "data_analysis": _perform_advanced_data_analysis(data_schema, data_summary),
        "domain_info": _identify_business_domain(data_schema, data_summary, user_responses),
        "user_pattern": _analyze_user_response_pattern(user_responses, {}),
        "step_definitions": _get_5step_definitions(),
        "data_schema": data_schema,
        "data_summary": data_summary
    }


def _generate_step_guidance(current_step: int, analysis_context: Dict[str, Any]) -> str:
    """현재 단계에 대한 질의 생성 가이드를 생성합니다."""
    step_definitions = analysis_context.get("step_definitions", [])
    domain_info = analysis_context.get("domain_info", {})
    data_analysis = analysis_context.get("data_analysis", {})
    user_pattern = analysis_context.get("user_pattern", {})
    
    if current_step <= len(step_definitions):
        step_info = step_definitions[current_step - 1]
        
        guidance = f"""
**{current_step}단계: {step_info['title']}**

**단계 설명:** {step_info['description']}

**데이터 분석 결과:**
- 식별된 도메인: {domain_info.get('primary_domain', '일반')} (신뢰도: {domain_info.get('domain_confidence', 0.0):.1%})
- 데이터 복잡도: {data_analysis.get('data_complexity', '중간')}
- 데이터 품질 점수: {data_analysis.get('data_quality_score', 0.5):.1%}

**사용자 패턴 분석:**
- 응답 스타일: {user_pattern.get('preference_style', '균형')}
- 기술 수준: {user_pattern.get('technical_level', '중간')}
- 상세도 선호: {user_pattern.get('detail_preference', '중간')}

**질의 생성 지침:**
위 분석 결과를 바탕으로 사용자에게 맞춤형 질의를 생성하세요. 도메인별 특화 내용과 사용자 패턴을 고려하여 구체적이고 실행 가능한 선택지를 제공하세요.
"""
        return guidance
    else:
        return "모든 질의 단계가 완료되었습니다. 수집된 정보를 바탕으로 리포트 생성을 진행할 수 있습니다."


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


def _perform_advanced_data_analysis(data_schema: Dict[str, str], data_summary: Dict[str, Any]) -> Dict[str, Any]:
    """고급 데이터 분석을 수행하여 더 정교한 인사이트를 도출합니다."""
    return {
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


# ===== 간단한 헬퍼 함수들 =====

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
        if isinstance(missing_values, dict):
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
    elif domain == "hr":
        insights["key_metrics"] = ["직원 만족도", "이직률", "성과 지표"]
        insights["recommended_analyses"] = ["부서별 성과 분석", "직원 세분화", "만족도 트렌드"]
        insights["business_questions"] = ["어떤 부서가 가장 성과가 좋은가?", "직원 만족도는 어떻게 되는가?"]
    
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


class QueryGenerationTool:
    def __init__(self):
        self.name = "generate_report_queries"
        self.description = "질의 생성을 위한 컨텍스트 정보를 제공하여 에이전트가 동적으로 질의를 생성할 수 있도록 지원합니다."
        self.input_model = QueryGenerationInput
        self.output_model = QueryGenerationOutput
        self.execute = generate_report_queries