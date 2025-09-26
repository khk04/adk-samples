"""리포트 평가 결과 저장 도구"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field
from google.adk.tools.function_tool import FunctionTool
import json
import os
from datetime import datetime


class ReportEvaluationSaverInput(BaseModel):
    """리포트 평가 결과 저장 입력"""
    report_name: str = Field(..., description="평가된 리포트 이름")
    evaluation_result: Dict[str, Any] = Field(..., description="평가 결과 데이터")
    report_content: str = Field(default="", description="평가된 리포트 내용")
    save_format: str = Field(default="both", description="저장 형식 (json, txt, both)")


class ReportEvaluationSaverOutput(BaseModel):
    """리포트 평가 결과 저장 출력"""
    success: bool = Field(..., description="저장 성공 여부")
    saved_files: List[str] = Field(default_factory=list, description="저장된 파일 경로 목록")
    message: str = Field(..., description="저장 결과 메시지")


@FunctionTool
def save_evaluation_result(
    report_name: str,
    evaluation_result: Dict[str, Any],
    report_content: str = "",
    save_format: str = "both"
) -> ReportEvaluationSaverOutput:
    """
    리포트 평가 결과를 파일로 저장합니다.
    
    저장 형식:
    - json: 구조화된 평가 데이터
    - txt: 사람이 읽기 쉬운 형태
    - both: 두 형식 모두 저장
    """
    try:
        # evaluations 디렉토리 생성
        evaluations_dir = "data/evaluations"
        os.makedirs(evaluations_dir, exist_ok=True)
        
        # 타임스탬프 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        saved_files = []
        
        # JSON 형식 저장
        if save_format in ["json", "both"]:
            json_filename = f"evaluation_{report_name}_{timestamp}.json"
            json_file_path = os.path.join(evaluations_dir, json_filename)
            
            # 평가 결과를 JSON 형태로 정리
            json_data = {
                "report_name": report_name,
                "evaluation_timestamp": timestamp,
                "overall_score": evaluation_result.get("overall_score", 0.0),
                "criteria_scores": evaluation_result.get("criteria_scores", {}),
                "strengths": evaluation_result.get("strengths", []),
                "improvements": evaluation_result.get("improvements", []),
                "recommendations": evaluation_result.get("recommendations", []),
                "detailed_feedback": evaluation_result.get("detailed_feedback", ""),
                "report_content": report_content
            }
            
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            saved_files.append(json_file_path)
        
        # TXT 형식 저장
        if save_format in ["txt", "both"]:
            txt_filename = f"evaluation_{report_name}_{timestamp}.txt"
            txt_file_path = os.path.join(evaluations_dir, txt_filename)
            
            # 사람이 읽기 쉬운 형태로 정리
            txt_content = _format_evaluation_for_txt(evaluation_result, report_name, timestamp)
            
            with open(txt_file_path, 'w', encoding='utf-8') as f:
                f.write(txt_content)
            
            saved_files.append(txt_file_path)
        
        # 저장 성공 메시지
        if len(saved_files) == 1:
            message = f"평가 결과가 성공적으로 저장되었습니다: {os.path.basename(saved_files[0])}"
        else:
            file_names = [os.path.basename(f) for f in saved_files]
            message = f"평가 결과가 성공적으로 저장되었습니다: {', '.join(file_names)}"
        
        return ReportEvaluationSaverOutput(
            success=True,
            saved_files=saved_files,
            message=message
        )
        
    except Exception as e:
        return ReportEvaluationSaverOutput(
            success=False,
            saved_files=[],
            message=f"평가 결과 저장 중 오류가 발생했습니다: {str(e)}"
        )


def _format_evaluation_for_txt(evaluation_result: Dict[str, Any], report_name: str, timestamp: str) -> str:
    """평가 결과를 TXT 형식으로 포맷팅합니다."""
    
    content_parts = []
    
    # 헤더
    content_parts.append("=" * 60)
    content_parts.append(f"리포트 품질 평가 결과")
    content_parts.append(f"리포트명: {report_name}")
    content_parts.append(f"평가 일시: {timestamp}")
    content_parts.append("=" * 60)
    content_parts.append("")
    
    # 전체 점수
    overall_score = evaluation_result.get("overall_score", 0.0)
    if overall_score >= 90:
        grade = "우수"
    elif overall_score >= 80:
        grade = "양호"
    elif overall_score >= 70:
        grade = "보통"
    else:
        grade = "개선필요"
    
    content_parts.append(f"📊 종합 평가 점수: {overall_score:.1f}/100점 (등급: {grade})")
    content_parts.append("")
    
    # 기준별 점수
    criteria_scores = evaluation_result.get("criteria_scores", {})
    if criteria_scores:
        content_parts.append("📈 기준별 점수:")
        content_parts.append(f"  - 완성도 (30%): {criteria_scores.get('completeness', 0.0):.1f}점")
        content_parts.append(f"  - 명확성 (25%): {criteria_scores.get('clarity', 0.0):.1f}점")
        content_parts.append(f"  - 정확성 (25%): {criteria_scores.get('accuracy', 0.0):.1f}점")
        content_parts.append(f"  - 구조 (20%): {criteria_scores.get('structure', 0.0):.1f}점")
        content_parts.append("")
    
    # 강점 분석
    strengths = evaluation_result.get("strengths", [])
    if strengths:
        content_parts.append("✅ 강점 분석:")
        for i, strength in enumerate(strengths, 1):
            content_parts.append(f"  {i}. {strength}")
        content_parts.append("")
    
    # 개선 제안
    improvements = evaluation_result.get("improvements", [])
    if improvements:
        content_parts.append("🔧 개선 제안:")
        for i, improvement in enumerate(improvements, 1):
            content_parts.append(f"  {i}. {improvement}")
        content_parts.append("")
    
    # 향후 권장사항
    recommendations = evaluation_result.get("recommendations", [])
    if recommendations:
        content_parts.append("💡 향후 권장사항:")
        for i, recommendation in enumerate(recommendations, 1):
            content_parts.append(f"  {i}. {recommendation}")
        content_parts.append("")
    
    # 상세 피드백
    detailed_feedback = evaluation_result.get("detailed_feedback", "")
    if detailed_feedback:
        content_parts.append("📋 상세 피드백:")
        content_parts.append(detailed_feedback)
        content_parts.append("")
    
    # 푸터
    content_parts.append("-" * 60)
    content_parts.append(f"이 평가는 {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}에 자동으로 생성되었습니다.")
    content_parts.append("=" * 60)
    
    return "\n".join(content_parts)


class ReportEvaluationSaver:
    def __init__(self):
        self.name = "save_evaluation_result"
        self.description = "리포트 평가 결과를 JSON과 TXT 형식으로 파일에 저장합니다."
        self.input_model = ReportEvaluationSaverInput
        self.output_model = ReportEvaluationSaverOutput
        self.execute = save_evaluation_result
