from google.adk.agents import Agent
from ...config import GENAI_MODEL
from ...prompt import REPORT_EVALUATION_PROMPT
from .tools.report_evaluation_tool import report_evaluation_tool


# 리포트 평가 에이전트
report_evaluation_agent = Agent(
    name="report_evaluation_agent",
    model=GENAI_MODEL,
    description="생성된 리포트의 품질을 4가지 기준으로 평가하는 전문가",
    instruction=REPORT_EVALUATION_PROMPT,
    tools=[report_evaluation_tool],
    output_key="evaluation_result"
)