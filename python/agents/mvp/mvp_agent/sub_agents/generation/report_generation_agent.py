from google.adk.agents import Agent
from ...config import GENAI_MODEL
from ...prompt import REPORT_GENERATION_PROMPT
from .tools.data_analysis_tool import data_analysis_tool, artifact_files_tool
from .tools.report_generation_tool import report_generation_tool


# 데이터 분석 및 리포트 생성 에이전트
data_analysis_report_agent = Agent(
    name="data_analysis_report_agent",
    model=GENAI_MODEL,
    description="다양한 형식의 데이터를 분석하여 한국어 비즈니스 리포트를 생성하는 전문가",
    instruction=REPORT_GENERATION_PROMPT,
    tools=[data_analysis_tool, artifact_files_tool, report_generation_tool],
    output_key="generated_report"
)