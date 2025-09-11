import json
from pathlib import Path
from google.adk.tools import ToolContext, FunctionTool
from ..config import QUALITY_WEIGHTS


def evaluate_report_quality(tool_context: ToolContext) -> dict:
    """
    생성된 리포트의 품질을 평가합니다.
    
    Args:
        tool_context: ADK 도구 컨텍스트
    
    Returns:
        dict: 리포트 품질 평가 결과
    """
    try:
        # 현재 리포트 정보 가져오기
        current_report = tool_context.state.get("current_report")
        if not current_report:
            return {
                "status": "error",
                "message": "평가할 리포트가 없습니다."
            }
        
        # 리포트 내용 가져오기
        report_content = current_report.get("content", "")
        
        # 각 기준별 점수 계산 (0-10점 척도)
        scores = {}
        
        # 1. 완성도 평가 (30% 가중치)
        completeness_score = evaluate_completeness(report_content)
        scores["completeness"] = {
            "score": completeness_score,
            "weight": QUALITY_WEIGHTS["completeness"],
            "reason": f"필수 섹션 포함도: {completeness_score}/10"
        }
        
        # 2. 명확성 평가 (25% 가중치)
        clarity_score = evaluate_clarity(report_content)
        scores["clarity"] = {
            "score": clarity_score,
            "weight": QUALITY_WEIGHTS["clarity"],
            "reason": f"문장 명확성 및 이해도: {clarity_score}/10"
        }
        
        # 3. 정확성 평가 (25% 가중치)
        accuracy_score = evaluate_accuracy(report_content)
        scores["accuracy"] = {
            "score": accuracy_score,
            "weight": QUALITY_WEIGHTS["accuracy"],
            "reason": f"데이터 분석 정확성: {accuracy_score}/10"
        }
        
        # 4. 구조 평가 (20% 가중치)
        structure_score = evaluate_structure(report_content)
        scores["structure"] = {
            "score": structure_score,
            "weight": QUALITY_WEIGHTS["structure"],
            "reason": f"리포트 구조 논리성: {structure_score}/10"
        }
        
        # 가중 평균 계산
        total_score = sum(
            scores[criterion]["score"] * scores[criterion]["weight"] 
            for criterion in scores
        )
        
        # 평가 결과를 세션 상태에 저장
        evaluation_result = {
            "total_score": round(total_score, 2),
            "scores": scores,
            "report_filename": current_report.get("filename"),
            "iteration": current_report.get("iteration")
        }
        
        tool_context.state["report_evaluation"] = evaluation_result
        
        return {
            "status": "success",
            "message": f"리포트 품질 평가 완료. 총점: {total_score:.2f}/10",
            "evaluation": evaluation_result
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"리포트 평가 중 오류 발생: {str(e)}"
        }


def evaluate_completeness(content: str) -> float:
    """완성도 평가 (필수 섹션 포함 여부)"""
    required_sections = ["요약", "주요 발견사항", "데이터 분석", "결론 및 권장사항"]
    found_sections = sum(1 for section in required_sections if section in content)
    return (found_sections / len(required_sections)) * 10


def evaluate_clarity(content: str) -> float:
    """명확성 평가 (문장 명확성 및 이해도)"""
    # 간단한 휴리스틱 기반 평가
    sentences = content.split('.')
    avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
    
    # 적절한 문장 길이 (10-20단어)를 기준으로 점수 계산
    if 10 <= avg_sentence_length <= 20:
        return 8.0
    elif 5 <= avg_sentence_length <= 30:
        return 6.0
    else:
        return 4.0


def evaluate_accuracy(content: str) -> float:
    """정확성 평가 (데이터 분석 정확성)"""
    # 숫자와 통계가 포함되어 있는지 확인
    import re
    numbers = re.findall(r'\d+', content)
    if len(numbers) >= 5:  # 충분한 수치 데이터 포함
        return 8.0
    elif len(numbers) >= 3:
        return 6.0
    else:
        return 4.0


def evaluate_structure(content: str) -> float:
    """구조 평가 (리포트 구조 논리성)"""
    # 섹션 구분자와 제목이 있는지 확인
    section_indicators = ["##", "**", "###", "-"]
    found_indicators = sum(1 for indicator in section_indicators if indicator in content)
    
    if found_indicators >= 3:
        return 8.0
    elif found_indicators >= 2:
        return 6.0
    else:
        return 4.0


# FunctionTool로 래핑
report_evaluation_tool = FunctionTool(func=evaluate_report_quality)