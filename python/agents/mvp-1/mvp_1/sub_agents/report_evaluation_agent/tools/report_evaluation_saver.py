"""리포트 평가 결과 저장 도구"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from google.adk.tools.function_tool import FunctionTool
import json
import os
from datetime import datetime


class ReportEvaluationSaveInput(BaseModel):
    """리포트 평가 결과 저장 입력"""
    report_file_path: str = Field(..., description="평가된 리포트 파일 경로")
    evaluation_result: Dict[str, Any] = Field(..., description="평가 결과 데이터")
    save_format: str = Field(default="json", description="저장 형식 (json, txt)")


class ReportEvaluationSaveOutput(BaseModel):
    """리포트 평가 결과 저장 출력"""
    saved_file_path: str = Field(..., description="저장된 평가 결과 파일 경로")
    success: bool = Field(..., description="저장 성공 여부")
    message: str = Field(..., description="처리 결과 메시지")


@FunctionTool
def save_report_evaluation(
    report_file_path: str,
    evaluation_result: Dict[str, Any],
    save_format: str = "json"
) -> ReportEvaluationSaveOutput:
    """
    리포트 평가 결과를 파일로 저장합니다.
    
    Args:
        report_file_path: 평가된 리포트 파일 경로
        evaluation_result: 평가 결과 데이터
        save_format: 저장 형식 (json, txt)
    
    Returns:
        ReportEvaluationSaveOutput: 저장 결과
    """
    try:
        # 평가 결과 디렉토리 생성
        current_dir = os.getcwd()
        evaluations_dir = os.path.join(current_dir, "data", "evaluations")
        os.makedirs(evaluations_dir, exist_ok=True)
        
        # 리포트 파일명에서 타임스탬프 추출 또는 현재 시간 사용
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 리포트 파일명 기반으로 평가 결과 파일명 생성
        report_basename = os.path.basename(report_file_path)
        report_name = os.path.splitext(report_basename)[0]
        
        if save_format.lower() == "json":
            file_path = os.path.join(evaluations_dir, f"evaluation_{report_name}_{timestamp}.json")
            
            # 평가 결과를 JSON으로 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(evaluation_result, f, ensure_ascii=False, indent=2)
                
        else:  # txt 형식
            file_path = os.path.join(evaluations_dir, f"evaluation_{report_name}_{timestamp}.txt")
            
            # 평가 결과를 텍스트로 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("=== 리포트 평가 결과 ===\n\n")
                f.write(f"평가 일시: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')}\n")
                f.write(f"리포트 파일: {report_file_path}\n\n")
                
                # 전체 점수
                f.write(f"전체 점수: {evaluation_result.get('overall_score', 0):.1f}/100\n\n")
                
                # 각 기준별 점수
                f.write("=== 기준별 점수 ===\n")
                section_scores = evaluation_result.get('section_scores', {})
                for criterion, score in section_scores.items():
                    f.write(f"- {criterion}: {score:.1f}/100\n")
                f.write("\n")
                
                # 필수 섹션 확인
                f.write("=== 필수 섹션 확인 ===\n")
                required_sections_check = evaluation_result.get('required_sections_check', {})
                for section, exists in required_sections_check.items():
                    status = "✅ 포함" if exists else "❌ 누락"
                    f.write(f"- {section}: {status}\n")
                f.write("\n")
                
                # 상세 피드백
                f.write("=== 상세 피드백 ===\n")
                detailed_feedback = evaluation_result.get('detailed_feedback', {})
                for criterion, feedback in detailed_feedback.items():
                    f.write(f"\n{criterion.upper()}:\n{feedback}\n")
                f.write("\n")
                
                # 개선 제안사항
                f.write("=== 개선 제안사항 ===\n")
                improvement_suggestions = evaluation_result.get('improvement_suggestions', [])
                for i, suggestion in enumerate(improvement_suggestions, 1):
                    f.write(f"{i}. {suggestion}\n")
        
        return ReportEvaluationSaveOutput(
            saved_file_path=file_path,
            success=True,
            message=f"평가 결과가 성공적으로 저장되었습니다: {file_path}"
        )
        
    except Exception as e:
        return ReportEvaluationSaveOutput(
            saved_file_path="",
            success=False,
            message=f"평가 결과 저장 중 오류가 발생했습니다: {str(e)}"
        )


class ReportEvaluationSaver:
    def __init__(self):
        self.name = "save_report_evaluation"
        self.description = "리포트 평가 결과를 파일로 저장합니다."
        self.input_model = ReportEvaluationSaveInput
        self.output_model = ReportEvaluationSaveOutput
        self.execute = save_report_evaluation
