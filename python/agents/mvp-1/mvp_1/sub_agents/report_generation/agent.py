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

"""Report generation sub-agent for creating final reports."""

from google.adk import Agent
from google.adk.tools.function_tool import FunctionTool
from typing import Dict, Any, List
from pydantic import BaseModel, Field
import json
from datetime import datetime
from . import prompt


class ReportGenerationInput(BaseModel):
    """리포트 생성 입력"""
    user_requirements: Dict[str, Any] = Field(..., description="사용자 요구사항")
    data_analysis: Dict[str, Any] = Field(..., description="데이터 분석 결과")
    report_specifications: Dict[str, Any] = Field(..., description="리포트 사양")


class ReportGenerationOutput(BaseModel):
    """리포트 생성 출력"""
    success: bool = Field(..., description="생성 성공 여부")
    report_content: str = Field(..., description="리포트 내용")
    report_structure: Dict[str, Any] = Field(default_factory=dict, description="리포트 구조")
    visualization_suggestions: List[str] = Field(default_factory=list, description="시각화 제안")
    next_steps: List[str] = Field(default_factory=list, description="다음 단계")
    error_message: str = Field(default="", description="오류 메시지")


@FunctionTool
def generate_business_report(
    user_requirements: Dict[str, Any],
    data_analysis: Dict[str, Any],
    report_specifications: Dict[str, Any]
) -> ReportGenerationOutput:
    """
    사용자 요구사항과 데이터 분석 결과를 바탕으로 전문적인 비즈니스 리포트를 생성합니다.
    """
    try:
        # 리포트 구조 생성
        report_structure = _create_report_structure(user_requirements, data_analysis)
        
        # 리포트 내용 생성
        report_content = _generate_report_content(
            user_requirements, 
            data_analysis, 
            report_specifications,
            report_structure
        )
        
        # 시각화 제안
        visualization_suggestions = _suggest_visualizations(data_analysis, user_requirements)
        
        # 다음 단계 제안
        next_steps = _suggest_next_steps(user_requirements, data_analysis)
        
        return ReportGenerationOutput(
            success=True,
            report_content=report_content,
            report_structure=report_structure,
            visualization_suggestions=visualization_suggestions,
            next_steps=next_steps
        )
        
    except Exception as e:
        return ReportGenerationOutput(
            success=False,
            error_message=f"리포트 생성 중 오류가 발생했습니다: {str(e)}"
        )


def _create_report_structure(user_requirements: Dict[str, Any], data_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """리포트 구조 생성"""
    structure = {
        "title": user_requirements.get("report_type", "데이터 분석 리포트"),
        "sections": [
            {
                "name": "요약",
                "description": "핵심 발견사항과 주요 인사이트 요약",
                "priority": "high"
            },
            {
                "name": "데이터 개요",
                "description": "분석된 데이터의 기본 정보와 특성",
                "priority": "medium"
            },
            {
                "name": "주요 분석 결과",
                "description": "데이터 분석을 통한 주요 발견사항",
                "priority": "high"
            },
            {
                "name": "비즈니스 인사이트",
                "description": "분석 결과를 비즈니스 관점에서 해석",
                "priority": "high"
            },
            {
                "name": "권장사항",
                "description": "데이터 기반 실행 가능한 권장사항",
                "priority": "high"
            }
        ]
    }
    
    # 데이터 품질 이슈가 있는 경우 추가 섹션
    if "data_quality_issues" in data_analysis and data_analysis["data_quality_issues"]:
        structure["sections"].append({
            "name": "데이터 품질 이슈",
            "description": "데이터 품질 관련 이슈 및 해결방안",
            "priority": "medium"
        })
    
    return structure


def _generate_report_content(
    user_requirements: Dict[str, Any],
    data_analysis: Dict[str, Any],
    report_specifications: Dict[str, Any],
    report_structure: Dict[str, Any]
) -> str:
    """리포트 내용 생성"""
    content_parts = []
    
    # 제목
    content_parts.append(f"# {report_structure['title']}")
    content_parts.append(f"**생성일:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    content_parts.append("")
    
    # 요약 섹션
    content_parts.append("## 📋 요약")
    if "business_insights" in data_analysis:
        content_parts.append("### 주요 발견사항")
        for insight in data_analysis["business_insights"][:3]:
            content_parts.append(f"- {insight}")
    
    if "analysis_recommendations" in data_analysis:
        content_parts.append("\n### 분석 권장사항")
        for rec in data_analysis["analysis_recommendations"][:3]:
            content_parts.append(f"- {rec}")
    
    content_parts.append("")
    
    # 데이터 개요 섹션
    content_parts.append("## 📊 데이터 개요")
    if "data_summary" in data_analysis:
        summary = data_analysis["data_summary"]
        content_parts.append(f"- **총 데이터 수:** {summary.get('total_rows', 'N/A'):,}행")
        content_parts.append(f"- **분석 컬럼 수:** {summary.get('total_columns', 'N/A')}개")
        content_parts.append(f"- **주요 컬럼:** {', '.join(summary.get('column_names', [])[:5])}")
    
    content_parts.append("")
    
    # 주요 분석 결과 섹션
    content_parts.append("## 🔍 주요 분석 결과")
    if "business_insights" in data_analysis:
        for i, insight in enumerate(data_analysis["business_insights"], 1):
            content_parts.append(f"### {i}. {insight}")
            content_parts.append("")
    
    # 비즈니스 인사이트 섹션
    content_parts.append("## 💡 비즈니스 인사이트")
    content_parts.append("분석 결과를 바탕으로 다음과 같은 비즈니스 인사이트를 도출했습니다:")
    content_parts.append("")
    
    if "analysis_recommendations" in data_analysis:
        for i, rec in enumerate(data_analysis["analysis_recommendations"], 1):
            content_parts.append(f"{i}. **{rec}**")
            content_parts.append("   - 데이터 분석을 통해 확인된 패턴을 바탕으로 한 권장사항")
            content_parts.append("")
    
    # 권장사항 섹션
    content_parts.append("## 🎯 권장사항")
    content_parts.append("### 즉시 실행 가능한 권장사항")
    content_parts.append("1. **데이터 모니터링 강화**")
    content_parts.append("   - 정기적인 데이터 품질 검토")
    content_parts.append("   - 핵심 지표 추적 시스템 구축")
    content_parts.append("")
    
    content_parts.append("2. **분석 프로세스 개선**")
    content_parts.append("   - 자동화된 리포트 생성 시스템 도입")
    content_parts.append("   - 데이터 기반 의사결정 프로세스 정립")
    content_parts.append("")
    
    # 데이터 품질 이슈 섹션
    if "data_quality_issues" in data_analysis and data_analysis["data_quality_issues"]:
        content_parts.append("## ⚠️ 데이터 품질 이슈")
        content_parts.append("다음과 같은 데이터 품질 이슈가 발견되었습니다:")
        content_parts.append("")
        for issue in data_analysis["data_quality_issues"]:
            content_parts.append(f"- {issue}")
        content_parts.append("")
        content_parts.append("### 해결방안")
        content_parts.append("1. 결측값 처리 방안 수립")
        content_parts.append("2. 데이터 수집 프로세스 개선")
        content_parts.append("3. 정기적인 데이터 검증 프로세스 도입")
        content_parts.append("")
    
    # 부록
    content_parts.append("## 📎 부록")
    content_parts.append("### 분석 방법론")
    content_parts.append("- 데이터 전처리: 결측값 및 이상치 처리")
    content_parts.append("- 통계 분석: 기술통계 및 분포 분석")
    content_parts.append("- 비즈니스 해석: 도메인 지식 기반 인사이트 도출")
    content_parts.append("")
    
    return "\n".join(content_parts)


def _suggest_visualizations(data_analysis: Dict[str, Any], user_requirements: Dict[str, Any]) -> List[str]:
    """시각화 제안"""
    suggestions = []
    
    if "data_summary" in data_analysis:
        summary = data_analysis["data_summary"]
        
        # 수치형 데이터가 있는 경우
        if "data_types" in summary:
            numeric_cols = [col for col, dtype in summary["data_types"].items() 
                          if dtype in ['int64', 'float64', 'int32', 'float32']]
            if numeric_cols:
                suggestions.append(f"수치형 데이터 분포 차트: {', '.join(numeric_cols[:3])}")
                suggestions.append("상관관계 히트맵")
        
        # 범주형 데이터가 있는 경우
        categorical_cols = [col for col, dtype in summary["data_types"].items() 
                          if dtype in ['object', 'category']]
        if categorical_cols:
            suggestions.append(f"범주별 분포 차트: {', '.join(categorical_cols[:3])}")
            suggestions.append("파이 차트 또는 막대 차트")
    
    # 리포트 스타일에 따른 추가 제안
    report_style = user_requirements.get("report_style", "")
    if "대시보드" in report_style:
        suggestions.append("인터랙티브 대시보드")
        suggestions.append("실시간 모니터링 차트")
    elif "상세 분석" in report_style:
        suggestions.append("시계열 차트")
        suggestions.append("박스 플롯")
        suggestions.append("산점도")
    
    return suggestions


def _suggest_next_steps(user_requirements: Dict[str, Any], data_analysis: Dict[str, Any]) -> List[str]:
    """다음 단계 제안"""
    next_steps = [
        "리포트 검토 및 피드백 수집",
        "핵심 지표 모니터링 시스템 구축",
        "정기적인 분석 일정 수립"
    ]
    
    # 데이터 품질 이슈가 있는 경우
    if "data_quality_issues" in data_analysis and data_analysis["data_quality_issues"]:
        next_steps.insert(0, "데이터 품질 개선 작업 우선 진행")
    
    # 분석 권장사항이 있는 경우
    if "analysis_recommendations" in data_analysis and data_analysis["analysis_recommendations"]:
        next_steps.append("추가 분석 영역 식별 및 실행")
    
    return next_steps


MODEL = "gemini-2.0-flash"

report_generation_agent = Agent(
    model=MODEL,
    name="report_generation_agent",
    instruction=prompt.REPORT_GENERATION_PROMPT,
    tools=[generate_business_report],
    output_key="report_results"
)