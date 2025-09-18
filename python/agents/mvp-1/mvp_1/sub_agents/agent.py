"""
리포트 평가 서브 에이전트

생성된 리포트의 품질을 평가하고 개선 제안을 제공하는 전용 에이전트입니다.
"""

from google.adk.agents import Agent
from google.adk.models import Gemini
from .tools.report_evaluation_tool import ReportEvaluationTool
from .tools.report_evaluation_saver import ReportEvaluationSaver
from .prompt import REPORT_EVALUATION_PROMPT
from ..config import DEFAULT_MODEL_NAME, DEFAULT_TEMPERATURE, DEFAULT_MAX_OUTPUT_TOKENS


def report_evaluation_agent() -> Agent:
    """
    리포트 품질 평가 전용 서브 에이전트를 생성합니다.
    
    이 에이전트는 생성된 리포트의 품질을 4가지 기준으로 평가하고,
    상세한 피드백과 개선 제안사항을 제공합니다.
    
    Returns:
        Agent: 구성된 리포트 평가 에이전트
    """
    
    # 모델 설정
    model = Gemini(
        model=DEFAULT_MODEL_NAME,
        temperature=DEFAULT_TEMPERATURE,
        max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS
    )
    
    # 도구 설정
    tools = [
        ReportEvaluationTool().execute,
        ReportEvaluationSaver().execute
    ]
    
    # 에이전트 생성
    agent = Agent(
        model=model,
        tools=tools,
        instruction=REPORT_EVALUATION_PROMPT,
        name="report_evaluation_agent",
        description="생성된 리포트의 품질을 평가하고 개선 제안을 제공하는 전용 에이전트"
    )
    
    return agent
