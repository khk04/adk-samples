"""
MVP-1: 사용자 데이터 기반 질의 생성 및 리포트 생성 에이전트

사용자 데이터를 분석하여 최적의 분석 질의를 생성하고, 동적 리포트를 생성하는 통합 에이전트입니다.

주요 구성요소:
- Gemini 모델 (gemini-2.5-flash)
- DataAnalysisTool: CSV/Excel 파일 분석
- QueryGenerationTool: 5단계 질의 생성
- DynamicReportGenerationAgent: 동적 리포트 생성
"""

from google.adk.agents import Agent
from google.adk.models import Gemini
from .prompt import QUERY_GENERATION_PROMPT
from .tools.data_analysis_tool import DataAnalysisTool
from .tools.query_generation_tool import QueryGenerationTool
from .tools.data_validation_tool import DataValidationTool
from .tools.user_data_check_tool import UserDataCheckTool
from .sub_agents.dynamic_report_generation import dynamic_report_generation_agent
from .config import DEFAULT_MODEL_NAME, DEFAULT_TEMPERATURE, DEFAULT_MAX_OUTPUT_TOKENS
import os


def query_generation_agent() -> Agent:
    """
    사용자 데이터 기반 질의 생성 및 리포트 생성 통합 에이전트를 생성합니다.
    
    이 에이전트는 사용자 데이터를 분석하여 최적의 분석 질의를 생성하기 위한
    5단계 질의를 자동으로 생성하고, 수집된 정보를 바탕으로 동적 리포트를 생성합니다.
    
    Returns:
        Agent: 구성된 질의 생성 및 리포트 생성 통합 에이전트
    """
    
    # 모델 설정
    model = Gemini(
        model=DEFAULT_MODEL_NAME,
        temperature=DEFAULT_TEMPERATURE,
        max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS
    )
    
    # 도구 설정 (질의 생성에 필요한 도구들)
    tools = [
        UserDataCheckTool().execute,
        DataValidationTool().execute,
        DataAnalysisTool().execute,
        QueryGenerationTool().execute
    ]
    
    # 서브 에이전트 설정 (리포트 생성용)
    sub_agents = [
        dynamic_report_generation_agent()
    ]
    
    # 에이전트 생성
    agent = Agent(
        model=model,
        tools=tools,
        sub_agents=sub_agents,
        instruction=QUERY_GENERATION_PROMPT,
        name="query_generation_agent",
        description="사용자 데이터를 분석하여 질의를 생성하고 리포트를 생성합니다"
    )
    
    return agent


# 루트 에이전트
root_agent = query_generation_agent()