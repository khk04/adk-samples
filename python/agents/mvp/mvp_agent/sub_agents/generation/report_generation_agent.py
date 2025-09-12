from google.adk.agents import Agent
from ...config import GENAI_MODEL
from ...prompt import REPORT_GENERATION_PROMPT
from .tools.data_analysis_tool import data_analysis_tool
from .tools.report_generation_tool import report_generation_tool
from ..evaluation.tools.file_reader_tool import (
    file_reader_tool, 
    file_list_tool, 
    latest_artifact_tool, 
    iteration_artifact_tool
)


# 데이터 분석 및 리포트 생성 에이전트
data_analysis_report_agent = Agent(
    name="data_analysis_report_agent",
    model=GENAI_MODEL,
    description="다양한 형식의 데이터를 분석하여 한국어 비즈니스 리포트를 생성하는 전문가",
    instruction=REPORT_GENERATION_PROMPT,
    tools=[
        data_analysis_tool, 
        report_generation_tool,
        file_reader_tool,
        file_list_tool,
        latest_artifact_tool,
        iteration_artifact_tool
    ],
    output_key="generated_report"
)