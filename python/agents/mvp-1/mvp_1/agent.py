"""
MVP-1: 사용자 데이터 기반 질의 생성 에이전트

사용자 데이터를 분석하여 최적의 리포트를 생성하기 위한 5단계 질의를 자동 생성하는 에이전트입니다.

주요 구성요소:
- Gemini 모델 (gemini-2.5-flash)
- DataAnalysisTool: CSV/Excel 파일 분석
- QueryGenerationTool: 5단계 질의 생성
"""

from google.adk.agents import Agent
from google.adk.models import Gemini
from .prompt import QUERY_GENERATION_PROMPT
from .tools.data_analysis_tool import DataAnalysisTool
from .tools.query_generation_tool import QueryGenerationTool
from .tools.data_validation_tool import DataValidationTool
from .tools.user_data_check_tool import UserDataCheckTool
from .config import DEFAULT_MODEL_NAME, DEFAULT_TEMPERATURE, DEFAULT_MAX_OUTPUT_TOKENS
import os


def query_generation_agent() -> Agent:
    """
    사용자 데이터 기반 질의 생성 에이전트를 생성합니다.
    
    이 에이전트는 사용자 데이터를 분석하여 최적의 리포트를 생성하기 위한
    5단계 질의를 자동으로 생성하고 진행합니다.
    
    Returns:
        Agent: 구성된 질의 생성 에이전트
    """
    
    # 모델 설정 - 명시적으로 gemini-2.5-flash 사용
    actual_model_name = "gemini-2.5-flash"  # 강제로 gemini-2.5-flash 사용
    
    print(f"🔧 모델 설정:")
    print(f"   - 강제 설정 모델: {actual_model_name}")
    print(f"   - .env GENAI_MODEL: {os.getenv('GENAI_MODEL')}")
    print(f"   - config.py 기본값: {DEFAULT_MODEL_NAME}")
    
    # Google ADK의 Gemini 클래스에서 model_name이 제대로 적용되지 않는 문제 해결
    # 여러 환경 변수로 모델 이름을 직접 설정
    os.environ['GEMINI_MODEL'] = actual_model_name
    os.environ['GOOGLE_GENAI_MODEL'] = actual_model_name
    os.environ['GENAI_MODEL'] = actual_model_name
    
    # 모델 생성 시 명시적으로 model 매개변수 사용
    model = Gemini(
        model=actual_model_name,  # model_name 대신 model 사용
        temperature=DEFAULT_TEMPERATURE,
        max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS
    )
    
    print(f"   - 설정된 환경 변수 GEMINI_MODEL: {os.environ.get('GEMINI_MODEL')}")
    print(f"   - 설정된 환경 변수 GOOGLE_GENAI_MODEL: {os.environ.get('GOOGLE_GENAI_MODEL')}")
    print(f"   - 설정된 환경 변수 GENAI_MODEL: {os.environ.get('GENAI_MODEL')}")
    
    # 도구 설정
    tools = [
        UserDataCheckTool().execute,
        DataValidationTool().execute,
        DataAnalysisTool().execute,
        QueryGenerationTool().execute
    ]
    
    # 에이전트 생성
    agent = Agent(
        model=model,
        tools=tools,
        instruction=QUERY_GENERATION_PROMPT,
        name="query_generation_agent",
        description="사용자 데이터를 분석하여 최적의 리포트 생성을 위한 5단계 질의를 자동 생성하는 에이전트"
    )
    
    return agent


# 루트 에이전트
root_agent = query_generation_agent()