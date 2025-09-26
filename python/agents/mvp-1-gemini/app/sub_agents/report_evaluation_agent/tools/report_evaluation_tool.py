"""리포트 품질 평가 도구"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field
from google.adk.tools.function_tool import FunctionTool


class ReportEvaluationInput(BaseModel):
    """리포트 평가 입력"""
    report_content: str = Field(..., description="평가할 리포트 내용")
    report_type: str = Field(default="comprehensive", description="리포트 유형")
    evaluation_criteria: Dict[str, Any] = Field(default_factory=dict, description="평가 기준")


class ReportEvaluationOutput(BaseModel):
    """리포트 평가 출력"""
    success: bool = Field(..., description="평가 성공 여부")
    overall_score: float = Field(..., description="전체 점수 (0-100)")
    criteria_scores: Dict[str, float] = Field(default_factory=dict, description="기준별 점수")
    strengths: List[str] = Field(default_factory=list, description="강점 분석")
    improvements: List[str] = Field(default_factory=list, description="개선 제안")
    recommendations: List[str] = Field(default_factory=list, description="향후 권장사항")
    detailed_feedback: str = Field(..., description="상세 피드백")


@FunctionTool
def evaluate_report_quality(
    report_content: str,
    report_type: str = "comprehensive",
    evaluation_criteria: Dict[str, Any] = {}
) -> ReportEvaluationOutput:
    """
    생성된 리포트의 품질을 종합적으로 평가합니다.
    
    평가 기준:
    1. 완성도 (30%): 필수 섹션 포함, 내용 충실도, 분석 구체성
    2. 명확성 (25%): 구조적 명확성, 문장 명확성, 용어 일관성
    3. 정확성 (25%): 수치 정확성, 논리적 일관성, 근거 충실성
    4. 구조 (20%): 헤더 구조, 목록/표 사용, 흐름과 연결성
    """
    try:
        # 리포트 구조 분석
        structure_analysis = _analyze_report_structure(report_content)
        
        # 내용 분석
        content_analysis = _analyze_report_content(report_content)
        
        # 필수 섹션 확인
        required_sections = _check_required_sections(report_content)
        
        # 기준별 점수 계산
        criteria_scores = _calculate_criteria_scores(
            structure_analysis, 
            content_analysis, 
            required_sections
        )
        
        # 전체 점수 계산 (가중치 적용)
        overall_score = (
            criteria_scores["completeness"] * 0.30 +
            criteria_scores["clarity"] * 0.25 +
            criteria_scores["accuracy"] * 0.25 +
            criteria_scores["structure"] * 0.20
        )
        
        # 강점 분석
        strengths = _identify_strengths(criteria_scores, structure_analysis, content_analysis)
        
        # 개선 제안
        improvements = _generate_improvements(criteria_scores, structure_analysis, content_analysis)
        
        # 향후 권장사항
        recommendations = _generate_recommendations(overall_score, report_type)
        
        # 상세 피드백 생성
        detailed_feedback = _generate_detailed_feedback(
            overall_score, criteria_scores, strengths, improvements, recommendations
        )
        
        return ReportEvaluationOutput(
            success=True,
            overall_score=overall_score,
            criteria_scores=criteria_scores,
            strengths=strengths,
            improvements=improvements,
            recommendations=recommendations,
            detailed_feedback=detailed_feedback
        )
        
    except Exception as e:
        return ReportEvaluationOutput(
            success=False,
            overall_score=0.0,
            detailed_feedback=f"리포트 평가 중 오류가 발생했습니다: {str(e)}"
        )


def _analyze_report_structure(report_content: str) -> Dict[str, Any]:
    """리포트 구조를 분석합니다."""
    lines = report_content.split('\n')
    
    structure = {
        "has_header": any(line.startswith('# ') for line in lines),
        "section_count": len([line for line in lines if line.startswith('##')]),
        "has_summary": any('요약' in line or 'summary' in line.lower() for line in lines),
        "has_conclusion": any('결론' in line or 'conclusion' in line.lower() for line in lines),
        "has_recommendations": any('권장' in line or 'recommendation' in line.lower() for line in lines),
        "has_tables": '|' in report_content,
        "has_lists": any(line.strip().startswith('-') or line.strip().startswith('*') for line in lines),
        "total_length": len(report_content),
        "average_section_length": 0
    }
    
    # 평균 섹션 길이 계산
    sections = [line for line in lines if line.startswith('##')]
    if len(sections) > 0:
        structure["average_section_length"] = len(report_content) / len(sections)
    
    return structure


def _analyze_report_content(report_content: str) -> Dict[str, Any]:
    """리포트 내용을 분석합니다."""
    content = {
        "has_data_analysis": any(word in report_content.lower() for word in ['분석', 'analysis', '통계', 'statistics']),
        "has_insights": any(word in report_content.lower() for word in ['인사이트', 'insight', '발견', 'finding']),
        "has_numbers": any(char.isdigit() for char in report_content),
        "has_charts_mentioned": any(word in report_content.lower() for word in ['차트', 'chart', '그래프', 'graph']),
        "technical_terms_count": sum(1 for word in ['분석', '통계', '모델', '알고리즘', '데이터', '인사이트'] if word in report_content),
        "readability_score": _calculate_readability_score(report_content)
    }
    
    return content


def _check_required_sections(report_content: str) -> Dict[str, bool]:
    """필수 섹션이 포함되어 있는지 확인합니다."""
    required_sections = {
        "summary": any('요약' in line or 'summary' in line.lower() for line in report_content.split('\n')),
        "key_findings": any('주요' in line and '발견' in line for line in report_content.split('\n')),
        "data_analysis": any('데이터' in line and '분석' in line for line in report_content.split('\n')),
        "conclusions": any('결론' in line or 'conclusion' in line.lower() for line in report_content.split('\n'))
    }
    
    return required_sections


def _calculate_criteria_scores(
    structure_analysis: Dict[str, Any], 
    content_analysis: Dict[str, Any], 
    required_sections: Dict[str, bool]
) -> Dict[str, float]:
    """기준별 점수를 계산합니다."""
    
    # 완성도 점수 (30%)
    completeness_score = 0.0
    
    # 필수 섹션 포함 (40점)
    included_sections = sum(1 for included in required_sections.values() if included)
    completeness_score += (included_sections / len(required_sections)) * 40
    
    # 내용 충실도 (30점)
    if content_analysis["total_length"] > 1000:
        completeness_score += 30
    elif content_analysis["total_length"] > 500:
        completeness_score += 20
    else:
        completeness_score += 10
    
    # 분석 구체성 (30점)
    if content_analysis["has_data_analysis"] and content_analysis["has_numbers"]:
        completeness_score += 30
    elif content_analysis["has_data_analysis"]:
        completeness_score += 20
    else:
        completeness_score += 10
    
    # 명확성 점수 (25%)
    clarity_score = 0.0
    
    # 구조적 명확성 (40점)
    if structure_analysis["has_header"] and structure_analysis["section_count"] >= 3:
        clarity_score += 40
    elif structure_analysis["has_header"]:
        clarity_score += 25
    else:
        clarity_score += 10
    
    # 문장 명확성 (30점)
    readability = content_analysis["readability_score"]
    clarity_score += readability * 30
    
    # 용어 일관성 (30점)
    if content_analysis["technical_terms_count"] >= 3:
        clarity_score += 30
    elif content_analysis["technical_terms_count"] >= 1:
        clarity_score += 20
    else:
        clarity_score += 10
    
    # 정확성 점수 (25%)
    accuracy_score = 0.0
    
    # 수치 데이터 정확성 (40점)
    if content_analysis["has_numbers"] and content_analysis["has_data_analysis"]:
        accuracy_score += 40
    elif content_analysis["has_numbers"]:
        accuracy_score += 25
    else:
        accuracy_score += 10
    
    # 논리적 일관성 (30점)
    if structure_analysis["has_conclusion"] and structure_analysis["has_recommendations"]:
        accuracy_score += 30
    elif structure_analysis["has_conclusion"]:
        accuracy_score += 20
    else:
        accuracy_score += 10
    
    # 근거 충실성 (30점)
    if content_analysis["has_insights"] and content_analysis["has_data_analysis"]:
        accuracy_score += 30
    elif content_analysis["has_insights"]:
        accuracy_score += 20
    else:
        accuracy_score += 10
    
    # 구조 점수 (20%)
    structure_score = 0.0
    
    # 헤더 구조 (40점)
    if structure_analysis["section_count"] >= 5:
        structure_score += 40
    elif structure_analysis["section_count"] >= 3:
        structure_score += 25
    else:
        structure_score += 10
    
    # 목록과 표 사용 (30점)
    if structure_analysis["has_tables"] and structure_analysis["has_lists"]:
        structure_score += 30
    elif structure_analysis["has_tables"] or structure_analysis["has_lists"]:
        structure_score += 20
    else:
        structure_score += 10
    
    # 흐름과 연결성 (30점)
    if structure_analysis["has_summary"] and structure_analysis["has_conclusion"]:
        structure_score += 30
    elif structure_analysis["has_summary"] or structure_analysis["has_conclusion"]:
        structure_score += 20
    else:
        structure_score += 10
    
    return {
        "completeness": min(completeness_score, 100.0),
        "clarity": min(clarity_score, 100.0),
        "accuracy": min(accuracy_score, 100.0),
        "structure": min(structure_score, 100.0)
    }


def _calculate_readability_score(text: str) -> float:
    """텍스트의 가독성을 계산합니다."""
    # 간단한 가독성 점수 계산 (0-1 범위)
    sentences = text.split('.')
    words = text.split()
    
    if len(sentences) == 0 or len(words) == 0:
        return 0.5
    
    avg_sentence_length = len(words) / len(sentences)
    
    # 평균 문장 길이가 적절하면 높은 점수
    if 10 <= avg_sentence_length <= 20:
        return 1.0
    elif 5 <= avg_sentence_length <= 25:
        return 0.8
    else:
        return 0.6


def _identify_strengths(
    criteria_scores: Dict[str, float], 
    structure_analysis: Dict[str, Any], 
    content_analysis: Dict[str, Any]
) -> List[str]:
    """강점을 식별합니다."""
    strengths = []
    
    # 완성도 강점
    if criteria_scores["completeness"] >= 80:
        strengths.append("리포트가 매우 완성도 높게 작성되었습니다.")
    elif criteria_scores["completeness"] >= 60:
        strengths.append("리포트의 전반적인 완성도가 양호합니다.")
    
    # 명확성 강점
    if criteria_scores["clarity"] >= 80:
        strengths.append("내용이 명확하고 이해하기 쉽게 작성되었습니다.")
    elif criteria_scores["clarity"] >= 60:
        strengths.append("구조적 명확성이 좋습니다.")
    
    # 정확성 강점
    if criteria_scores["accuracy"] >= 80:
        strengths.append("데이터 분석의 정확성과 논리적 일관성이 뛰어납니다.")
    elif criteria_scores["accuracy"] >= 60:
        strengths.append("분석 결과의 신뢰성이 높습니다.")
    
    # 구조 강점
    if criteria_scores["structure"] >= 80:
        strengths.append("리포트 구조가 체계적이고 논리적입니다.")
    elif criteria_scores["structure"] >= 60:
        strengths.append("구조적 구성이 양호합니다.")
    
    # 특별한 강점들
    if structure_analysis["has_tables"]:
        strengths.append("표를 활용한 데이터 제시가 효과적입니다.")
    
    if content_analysis["has_insights"]:
        strengths.append("실용적인 인사이트가 잘 도출되었습니다.")
    
    return strengths


def _generate_improvements(
    criteria_scores: Dict[str, float], 
    structure_analysis: Dict[str, Any], 
    content_analysis: Dict[str, Any]
) -> List[str]:
    """개선 제안을 생성합니다."""
    improvements = []
    
    # 완성도 개선
    if criteria_scores["completeness"] < 70:
        improvements.append("필수 섹션들을 모두 포함하여 리포트의 완성도를 높이세요.")
    
    # 명확성 개선
    if criteria_scores["clarity"] < 70:
        improvements.append("문장을 더 간결하고 명확하게 작성하세요.")
    
    # 정확성 개선
    if criteria_scores["accuracy"] < 70:
        improvements.append("데이터 분석의 정확성을 높이고 근거를 더 충실히 제시하세요.")
    
    # 구조 개선
    if criteria_scores["structure"] < 70:
        improvements.append("헤더를 활용한 체계적인 구성과 목록/표를 활용하세요.")
    
    # 특별한 개선사항들
    if not structure_analysis["has_tables"] and content_analysis["has_numbers"]:
        improvements.append("수치 데이터를 표로 정리하여 가독성을 높이세요.")
    
    if content_analysis["technical_terms_count"] < 2:
        improvements.append("전문 용어를 적절히 사용하여 분석의 깊이를 높이세요.")
    
    return improvements


def _generate_recommendations(overall_score: float, report_type: str) -> List[str]:
    """향후 권장사항을 생성합니다."""
    recommendations = []
    
    if overall_score >= 85:
        recommendations.extend([
            "매우 우수한 리포트입니다. 이 수준을 유지하세요.",
            "더 복잡한 분석 기법을 도입하여 인사이트를 심화하세요.",
            "시각화 요소를 추가하여 이해도를 높이세요."
        ])
    elif overall_score >= 70:
        recommendations.extend([
            "양호한 리포트입니다. 일부 영역을 개선하면 더욱 우수해질 것입니다.",
            "데이터 분석의 깊이를 더욱 높여보세요.",
            "실행 가능한 구체적 권장사항을 더 많이 포함하세요."
        ])
    else:
        recommendations.extend([
            "리포트의 전반적인 품질 개선이 필요합니다.",
            "구조적 완성도를 높이고 내용을 더 체계적으로 정리하세요.",
            "데이터 분석 방법론을 개선하여 신뢰성을 높이세요."
        ])
    
    return recommendations


def _generate_detailed_feedback(
    overall_score: float,
    criteria_scores: Dict[str, float],
    strengths: List[str],
    improvements: List[str],
    recommendations: List[str]
) -> str:
    """상세 피드백을 생성합니다."""
    
    feedback_parts = []
    
    # 전체 점수 및 등급
    if overall_score >= 90:
        grade = "우수"
    elif overall_score >= 80:
        grade = "양호"
    elif overall_score >= 70:
        grade = "보통"
    else:
        grade = "개선필요"
    
    feedback_parts.append(f"📊 **종합 평가 점수: {overall_score:.1f}/100점 (등급: {grade})**")
    feedback_parts.append("")
    
    # 기준별 점수
    feedback_parts.append("📈 **기준별 점수:**")
    feedback_parts.append(f"- 완성도: {criteria_scores['completeness']:.1f}/100점")
    feedback_parts.append(f"- 명확성: {criteria_scores['clarity']:.1f}/100점")
    feedback_parts.append(f"- 정확성: {criteria_scores['accuracy']:.1f}/100점")
    feedback_parts.append(f"- 구조: {criteria_scores['structure']:.1f}/100점")
    feedback_parts.append("")
    
    # 강점 분석
    if strengths:
        feedback_parts.append("✅ **강점 분석:**")
        for i, strength in enumerate(strengths, 1):
            feedback_parts.append(f"{i}. {strength}")
        feedback_parts.append("")
    
    # 개선 제안
    if improvements:
        feedback_parts.append("🔧 **개선 제안:**")
        for i, improvement in enumerate(improvements, 1):
            feedback_parts.append(f"{i}. {improvement}")
        feedback_parts.append("")
    
    # 향후 권장사항
    if recommendations:
        feedback_parts.append("💡 **향후 권장사항:**")
        for i, recommendation in enumerate(recommendations, 1):
            feedback_parts.append(f"{i}. {recommendation}")
    
    return "\n".join(feedback_parts)


class ReportEvaluationTool:
    def __init__(self):
        self.name = "evaluate_report_quality"
        self.description = "생성된 리포트의 품질을 종합적으로 평가하여 강점, 개선사항, 권장사항을 제시합니다."
        self.input_model = ReportEvaluationInput
        self.output_model = ReportEvaluationOutput
        self.execute = evaluate_report_quality
