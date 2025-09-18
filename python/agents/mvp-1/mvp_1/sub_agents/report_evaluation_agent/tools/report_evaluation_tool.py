"""리포트 평가 도구"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from google.adk.tools.function_tool import FunctionTool
import re
import os
from datetime import datetime


class ReportEvaluationInput(BaseModel):
    """리포트 평가 입력"""
    report_content: str = Field(..., description="평가할 리포트 내용")
    report_file_path: str = Field(default="", description="리포트 파일 경로 (선택사항)")
    evaluation_criteria: Dict[str, float] = Field(
        default={
            "completeness": 0.30,  # 완성도 30%
            "clarity": 0.25,       # 명확성 25%
            "accuracy": 0.25,      # 정확성 25%
            "structure": 0.20      # 구조 20%
        },
        description="평가 기준 가중치"
    )
    required_sections: List[str] = Field(
        default=["요약", "주요 발견사항", "데이터 분석", "결론 및 권장사항"],
        description="필수 섹션 목록"
    )


class ReportEvaluationOutput(BaseModel):
    """리포트 평가 출력"""
    overall_score: float = Field(..., description="전체 점수 (0-100)")
    section_scores: Dict[str, float] = Field(..., description="각 평가 기준별 점수")
    required_sections_check: Dict[str, bool] = Field(..., description="필수 섹션 존재 여부")
    detailed_feedback: Dict[str, str] = Field(..., description="각 기준별 상세 피드백")
    improvement_suggestions: List[str] = Field(..., description="개선 제안사항")
    success: bool = Field(..., description="평가 성공 여부")
    message: str = Field(..., description="처리 결과 메시지")


@FunctionTool
def evaluate_report_quality(
    report_content: str,
    report_file_path: str = "",
    evaluation_criteria: Dict[str, float] = {
        "completeness": 0.30,
        "clarity": 0.25,
        "accuracy": 0.25,
        "structure": 0.20
    },
    required_sections: List[str] = ["요약", "주요 발견사항", "데이터 분석", "결론 및 권장사항"]
) -> ReportEvaluationOutput:
    """
    생성된 리포트의 품질을 평가합니다.
    
    Args:
        report_content: 평가할 리포트 내용
        report_file_path: 리포트 파일 경로 (선택사항)
        evaluation_criteria: 평가 기준 가중치
        required_sections: 필수 섹션 목록
    
    Returns:
        ReportEvaluationOutput: 평가 결과
    """
    try:
        # 리포트 파일에서 내용 읽기 (파일 경로가 제공된 경우)
        if report_file_path and os.path.exists(report_file_path):
            try:
                with open(report_file_path, 'r', encoding='utf-8') as f:
                    report_content = f.read()
            except Exception as e:
                print(f"파일 읽기 실패: {e}")
        
        if not report_content:
            return ReportEvaluationOutput(
                overall_score=0.0,
                section_scores={},
                required_sections_check={},
                detailed_feedback={},
                improvement_suggestions=["리포트 내용이 비어있습니다."],
                success=False,
                message="평가할 리포트 내용이 없습니다."
            )
        
        # 각 평가 기준별 점수 계산
        section_scores = {}
        detailed_feedback = {}
        
        # 1. 완성도 평가 (completeness)
        completeness_score, completeness_feedback = _evaluate_completeness(report_content, required_sections)
        section_scores["completeness"] = completeness_score
        detailed_feedback["completeness"] = completeness_feedback
        
        # 2. 명확성 평가 (clarity)
        clarity_score, clarity_feedback = _evaluate_clarity(report_content)
        section_scores["clarity"] = clarity_score
        detailed_feedback["clarity"] = clarity_feedback
        
        # 3. 정확성 평가 (accuracy)
        accuracy_score, accuracy_feedback = _evaluate_accuracy(report_content)
        section_scores["accuracy"] = accuracy_score
        detailed_feedback["accuracy"] = accuracy_feedback
        
        # 4. 구조 평가 (structure)
        structure_score, structure_feedback = _evaluate_structure(report_content)
        section_scores["structure"] = structure_score
        detailed_feedback["structure"] = structure_feedback
        
        # 필수 섹션 확인
        required_sections_check = _check_required_sections(report_content, required_sections)
        
        # 전체 점수 계산 (가중치 적용)
        overall_score = sum(
            section_scores[criterion] * weight 
            for criterion, weight in evaluation_criteria.items()
            if criterion in section_scores
        )
        
        # 개선 제안사항 생성
        improvement_suggestions = _generate_improvement_suggestions(
            section_scores, required_sections_check, detailed_feedback
        )
        
        return ReportEvaluationOutput(
            overall_score=round(overall_score, 2),
            section_scores=section_scores,
            required_sections_check=required_sections_check,
            detailed_feedback=detailed_feedback,
            improvement_suggestions=improvement_suggestions,
            success=True,
            message=f"리포트 평가가 완료되었습니다. 전체 점수: {overall_score:.1f}/100"
        )
        
    except Exception as e:
        return ReportEvaluationOutput(
            overall_score=0.0,
            section_scores={},
            required_sections_check={},
            detailed_feedback={},
            improvement_suggestions=[f"평가 중 오류 발생: {str(e)}"],
            success=False,
            message=f"리포트 평가 중 오류가 발생했습니다: {str(e)}"
        )


def _evaluate_completeness(report_content: str, required_sections: List[str]) -> tuple[float, str]:
    """완성도 평가"""
    score = 0.0
    feedback_parts = []
    
    # 1. 필수 섹션 존재 여부 (40점)
    missing_sections = []
    for section in required_sections:
        if not _section_exists(report_content, section):
            missing_sections.append(section)
    
    if not missing_sections:
        score += 40
        feedback_parts.append("✅ 모든 필수 섹션이 포함되어 있습니다.")
    else:
        missing_count = len(missing_sections)
        section_score = max(0, 40 - (missing_count * 10))
        score += section_score
        feedback_parts.append(f"⚠️ 누락된 필수 섹션: {', '.join(missing_sections)}")
    
    # 2. 내용의 충실도 (30점)
    content_length = len(report_content.strip())
    if content_length > 2000:
        score += 30
        feedback_parts.append("✅ 충분한 내용이 포함되어 있습니다.")
    elif content_length > 1000:
        score += 20
        feedback_parts.append("⚠️ 내용이 다소 부족할 수 있습니다.")
    else:
        score += 10
        feedback_parts.append("❌ 내용이 부족합니다.")
    
    # 3. 데이터 분석의 구체성 (30점)
    data_indicators = [
        "평균", "총합", "비율", "증가", "감소", "분석", "통계", 
        "데이터", "결과", "수치", "백분율", "%"
    ]
    
    data_mentions = sum(1 for indicator in data_indicators if indicator in report_content)
    if data_mentions >= 5:
        score += 30
        feedback_parts.append("✅ 구체적인 데이터 분석이 포함되어 있습니다.")
    elif data_mentions >= 3:
        score += 20
        feedback_parts.append("⚠️ 데이터 분석이 다소 부족합니다.")
    else:
        score += 10
        feedback_parts.append("❌ 구체적인 데이터 분석이 부족합니다.")
    
    feedback = " ".join(feedback_parts)
    return min(100, score), feedback


def _evaluate_clarity(report_content: str) -> tuple[float, str]:
    """명확성 평가"""
    score = 0.0
    feedback_parts = []
    
    # 1. 구조적 명확성 (40점)
    headers = re.findall(r'^#{1,6}\s+(.+)$', report_content, re.MULTILINE)
    if len(headers) >= 4:
        score += 40
        feedback_parts.append("✅ 명확한 구조로 구성되어 있습니다.")
    elif len(headers) >= 2:
        score += 25
        feedback_parts.append("⚠️ 구조가 다소 단순합니다.")
    else:
        score += 10
        feedback_parts.append("❌ 구조가 불명확합니다.")
    
    # 2. 문장의 명확성 (30점)
    sentences = re.split(r'[.!?]', report_content)
    long_sentences = [s for s in sentences if len(s.strip()) > 100]
    
    if len(long_sentences) == 0:
        score += 30
        feedback_parts.append("✅ 문장이 명확하고 이해하기 쉽습니다.")
    elif len(long_sentences) <= 2:
        score += 20
        feedback_parts.append("⚠️ 일부 문장이 길어 이해하기 어려울 수 있습니다.")
    else:
        score += 10
        feedback_parts.append("❌ 문장이 너무 길어 가독성이 떨어집니다.")
    
    # 3. 용어의 일관성 (30점)
    # 반복되는 키워드 확인
    words = re.findall(r'\b\w+\b', report_content.lower())
    word_freq = {}
    for word in words:
        if len(word) > 3:  # 3글자 이상 단어만
            word_freq[word] = word_freq.get(word, 0) + 1
    
    consistent_terms = sum(1 for freq in word_freq.values() if freq >= 3)
    if consistent_terms >= 3:
        score += 30
        feedback_parts.append("✅ 핵심 용어가 일관되게 사용되었습니다.")
    elif consistent_terms >= 1:
        score += 20
        feedback_parts.append("⚠️ 용어 사용의 일관성이 다소 부족합니다.")
    else:
        score += 10
        feedback_parts.append("❌ 용어 사용이 일관되지 않습니다.")
    
    feedback = " ".join(feedback_parts)
    return min(100, score), feedback


def _evaluate_accuracy(report_content: str) -> tuple[float, str]:
    """정확성 평가"""
    score = 0.0
    feedback_parts = []
    
    # 1. 수치 데이터의 정확성 (40점)
    numbers = re.findall(r'\d+\.?\d*', report_content)
    percentages = re.findall(r'\d+\.?\d*%', report_content)
    
    if len(numbers) >= 5 and len(percentages) >= 2:
        score += 40
        feedback_parts.append("✅ 구체적인 수치 데이터가 포함되어 있습니다.")
    elif len(numbers) >= 3:
        score += 25
        feedback_parts.append("⚠️ 수치 데이터가 다소 부족합니다.")
    else:
        score += 10
        feedback_parts.append("❌ 구체적인 수치 데이터가 부족합니다.")
    
    # 2. 논리적 일관성 (30점)
    # 모순되는 표현 확인
    contradictions = [
        ("증가", "감소"), ("높다", "낮다"), ("많다", "적다"),
        ("상승", "하락"), ("개선", "악화")
    ]
    
    contradiction_count = 0
    for pos, neg in contradictions:
        if pos in report_content and neg in report_content:
            contradiction_count += 1
    
    if contradiction_count == 0:
        score += 30
        feedback_parts.append("✅ 논리적으로 일관된 내용입니다.")
    elif contradiction_count <= 1:
        score += 20
        feedback_parts.append("⚠️ 일부 논리적 불일치가 있을 수 있습니다.")
    else:
        score += 10
        feedback_parts.append("❌ 논리적 일관성에 문제가 있습니다.")
    
    # 3. 근거의 충실성 (30점)
    evidence_indicators = [
        "분석 결과", "데이터에 따르면", "통계적으로", "조사 결과",
        "근거", "증거", "확인", "검증"
    ]
    
    evidence_count = sum(1 for indicator in evidence_indicators if indicator in report_content)
    if evidence_count >= 3:
        score += 30
        feedback_parts.append("✅ 충분한 근거가 제시되었습니다.")
    elif evidence_count >= 1:
        score += 20
        feedback_parts.append("⚠️ 근거 제시가 다소 부족합니다.")
    else:
        score += 10
        feedback_parts.append("❌ 근거 제시가 부족합니다.")
    
    feedback = " ".join(feedback_parts)
    return min(100, score), feedback


def _evaluate_structure(report_content: str) -> tuple[float, str]:
    """구조 평가"""
    score = 0.0
    feedback_parts = []
    
    # 1. 헤더 구조 (40점)
    headers = re.findall(r'^#{1,6}\s+(.+)$', report_content, re.MULTILINE)
    h1_count = len([h for h in headers if h.startswith('# ')])
    h2_count = len([h for h in headers if h.startswith('## ')])
    
    if h1_count >= 1 and h2_count >= 3:
        score += 40
        feedback_parts.append("✅ 적절한 헤더 구조를 가지고 있습니다.")
    elif h2_count >= 2:
        score += 25
        feedback_parts.append("⚠️ 헤더 구조가 다소 단순합니다.")
    else:
        score += 10
        feedback_parts.append("❌ 헤더 구조가 부족합니다.")
    
    # 2. 목록과 표 사용 (30점)
    list_items = len(re.findall(r'^\s*[-*+]\s+', report_content, re.MULTILINE))
    table_rows = len(re.findall(r'\|.*\|', report_content))
    
    if list_items >= 5 or table_rows >= 3:
        score += 30
        feedback_parts.append("✅ 목록과 표를 효과적으로 활용했습니다.")
    elif list_items >= 3 or table_rows >= 1:
        score += 20
        feedback_parts.append("⚠️ 목록과 표 활용이 다소 부족합니다.")
    else:
        score += 10
        feedback_parts.append("❌ 목록과 표 활용이 부족합니다.")
    
    # 3. 흐름과 연결성 (30점)
    transition_words = [
        "또한", "그러나", "따라서", "결론적으로", "또한", "더불어",
        "반면", "한편", "특히", "예를 들어", "즉", "따라서"
    ]
    
    transition_count = sum(1 for word in transition_words if word in report_content)
    if transition_count >= 3:
        score += 30
        feedback_parts.append("✅ 내용 간 연결이 자연스럽습니다.")
    elif transition_count >= 1:
        score += 20
        feedback_parts.append("⚠️ 내용 간 연결이 다소 부족합니다.")
    else:
        score += 10
        feedback_parts.append("❌ 내용 간 연결이 부족합니다.")
    
    feedback = " ".join(feedback_parts)
    return min(100, score), feedback


def _check_required_sections(report_content: str, required_sections: List[str]) -> Dict[str, bool]:
    """필수 섹션 존재 여부 확인"""
    section_check = {}
    
    for section in required_sections:
        section_check[section] = _section_exists(report_content, section)
    
    return section_check


def _section_exists(report_content: str, section_name: str) -> bool:
    """특정 섹션이 존재하는지 확인"""
    # 다양한 형태의 섹션명 검색
    patterns = [
        f"#+\\s*{section_name}",
        f"#+\\s*.*{section_name}.*",
        f"##+\\s*{section_name}",
        f"##+\\s*.*{section_name}.*"
    ]
    
    for pattern in patterns:
        if re.search(pattern, report_content, re.IGNORECASE):
            return True
    
    # 키워드 기반 검색
    keywords = {
        "요약": ["요약", "개요", "summary", "overview"],
        "주요 발견사항": ["주요", "발견", "결과", "findings", "key"],
        "데이터 분석": ["분석", "데이터", "analysis", "data"],
        "결론 및 권장사항": ["결론", "권장", "제안", "conclusion", "recommendation"]
    }
    
    if section_name in keywords:
        for keyword in keywords[section_name]:
            if keyword in report_content:
                return True
    
    return False


def _generate_improvement_suggestions(
    section_scores: Dict[str, float], 
    required_sections_check: Dict[str, bool],
    detailed_feedback: Dict[str, str]
) -> List[str]:
    """개선 제안사항 생성"""
    suggestions = []
    
    # 낮은 점수 기준별 개선 제안
    for criterion, score in section_scores.items():
        if score < 60:
            if criterion == "completeness":
                suggestions.append("📝 완성도 개선: 누락된 필수 섹션을 추가하고 내용을 더 풍부하게 작성하세요.")
            elif criterion == "clarity":
                suggestions.append("📖 명확성 개선: 문장을 더 간결하게 하고 구조를 명확히 하세요.")
            elif criterion == "accuracy":
                suggestions.append("📊 정확성 개선: 구체적인 수치 데이터와 근거를 더 많이 포함하세요.")
            elif criterion == "structure":
                suggestions.append("🏗️ 구조 개선: 헤더를 활용한 체계적인 구성과 목록/표를 활용하세요.")
    
    # 누락된 필수 섹션에 대한 제안
    missing_sections = [section for section, exists in required_sections_check.items() if not exists]
    if missing_sections:
        suggestions.append(f"📋 필수 섹션 추가: {', '.join(missing_sections)} 섹션을 추가하세요.")
    
    # 전체적인 개선 제안
    overall_score = sum(section_scores.values()) / len(section_scores)
    if overall_score < 70:
        suggestions.append("🎯 전반적인 품질 향상: 데이터 분석의 깊이를 높이고 구체적인 인사이트를 제시하세요.")
    
    if not suggestions:
        suggestions.append("🎉 리포트 품질이 우수합니다! 현재 수준을 유지하세요.")
    
    return suggestions


class ReportEvaluationTool:
    def __init__(self):
        self.name = "evaluate_report_quality"
        self.description = "생성된 리포트의 품질을 평가하고 개선 제안을 제공합니다."
        self.input_model = ReportEvaluationInput
        self.output_model = ReportEvaluationOutput
        self.execute = evaluate_report_quality
