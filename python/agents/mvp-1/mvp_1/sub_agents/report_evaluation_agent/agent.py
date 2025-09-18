"""
리포트 평가 서브 에이전트

생성된 리포트의 품질을 평가하고 개선 사항을 제안하는 전용 에이전트입니다.
"""

from google.adk.agents import Agent
from google.adk.models import Gemini
from .tools.report_evaluation_tool import ReportEvaluationTool
from .tools.report_evaluation_saver import ReportEvaluationSaver
from ...config import DEFAULT_MODEL_NAME, DEFAULT_TEMPERATURE, DEFAULT_MAX_OUTPUT_TOKENS


def report_evaluation_agent() -> Agent:
    """
    리포트 평가 전용 서브 에이전트를 생성합니다.
    
    이 에이전트는 생성된 리포트의 품질을 평가하고
    개선 사항을 제안하며 평가 결과를 저장합니다.
    
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
        description="생성된 리포트의 품질을 평가하고 개선 사항을 제안하는 전용 에이전트"
    )
    
    return agent


# 리포트 평가 프롬프트
REPORT_EVALUATION_PROMPT = """
당신은 리포트 품질 평가 전문가입니다.

주요 역할:
1. 생성된 리포트의 품질을 종합적으로 평가
2. 데이터 분석의 정확성과 논리성 검증
3. 인사이트의 유용성과 실용성 평가
4. 리포트 구조와 가독성 분석
5. 개선 사항과 권장사항 제시

평가 기준:
- 데이터 정확성: 분석 결과의 정확성과 신뢰성
- 논리적 일관성: 결론과 근거의 논리적 연결
- 실용성: 비즈니스 의사결정에 도움이 되는 정도
- 가독성: 리포트의 구조와 표현의 명확성
- 혁신성: 새로운 관점이나 인사이트 제공 여부

평가 결과는 객관적이고 구체적으로 제시하며, 개선 방향을 명확히 제시해주세요.
"""