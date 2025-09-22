"""
동적 리포트 생성 서브 에이전트

데이터 특성과 사용자 요청에 따라 동적으로 맞춤형 리포트를 생성하는 전용 에이전트입니다.
"""

from google.adk.agents import Agent
from google.adk.models import Gemini
from .tools.domain_analyzer_tool import DomainAnalyzerTool
from .tools.dynamic_analysis_tool import DynamicAnalysisTool
from .tools.insight_generator_tool import InsightGeneratorTool
from .tools.recommendation_tool import RecommendationTool
from .tools.report_file_generator_tool import ReportFileGeneratorTool
from .tools.visualization_generator_tool import VisualizationGeneratorTool
from .prompt import DYNAMIC_REPORT_GENERATION_PROMPT
from ...config import DEFAULT_MODEL_NAME, DEFAULT_TEMPERATURE, DEFAULT_MAX_OUTPUT_TOKENS


def dynamic_report_generation_agent() -> Agent:
    """
    동적 리포트 생성 전용 서브 에이전트를 생성합니다.
    
    이 에이전트는 데이터의 특성과 사용자 요청을 분석하여
    각 비즈니스 도메인에 최적화된 맞춤형 리포트를 생성하고
    실제 파일로 저장합니다.
    
    Returns:
        Agent: 구성된 동적 리포트 생성 에이전트
    """
    
    # 모델 설정
    model = Gemini(
        model=DEFAULT_MODEL_NAME,
        temperature=DEFAULT_TEMPERATURE,
        max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS
    )
    
    # 도구 설정
    tools = [
        DomainAnalyzerTool().execute,
        DynamicAnalysisTool().execute,
        InsightGeneratorTool().execute,
        RecommendationTool().execute,
        VisualizationGeneratorTool().execute,
        ReportFileGeneratorTool().execute
    ]
    
    # 에이전트 생성
    agent = Agent(
        model=model,
        tools=tools,
        instruction=DYNAMIC_REPORT_GENERATION_PROMPT,
        name="dynamic_report_generation_agent",
        description="데이터를 분석하여 맞춤형 리포트를 생성합니다"
    )
    
    return agent