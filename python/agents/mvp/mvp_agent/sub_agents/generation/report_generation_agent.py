from google.adk.agents import Agent
from ...config import GENAI_MODEL
from ...prompt import REPORT_GENERATION_PROMPT
from .tools.csv_analysis_tool import csv_analysis_tool
from .tools.report_generation_tool import report_generation_tool


# 리포트 생성 에이전트
report_generation_agent = Agent(
    name="report_generation_agent",
    model=GENAI_MODEL,
    description="CSV 데이터를 분석하여 한국어 비즈니스 리포트를 생성하는 전문가",
    instruction=REPORT_GENERATION_PROMPT,
    tools=[csv_analysis_tool, report_generation_tool],
    output_key="generated_report"
)