from google.adk.agents import Agent
from ...config import GENAI_MODEL
from .prompt import ARTIFACT_SAVE_PROMPT
from .tools.artifact_save_tool import (
    artifact_save_tool, 
    multiple_artifact_save_tool, 
    artifact_list_tool
)
from .tools.file_processor_tool import (
    file_type_detector_tool,
    pdf_processor_tool,
    csv_processor_tool,
    universal_file_processor_tool
)


# 아티팩트 저장 에이전트
artifact_save_agent = Agent(
    name="artifact_save_agent",
    model=GENAI_MODEL,
    description="아티팩트 내용을 파일로 저장하고 PDF/CSV 파일을 처리하는 전문가입니다.",
    instruction=ARTIFACT_SAVE_PROMPT,
    tools=[
        # 아티팩트 저장 도구
        artifact_save_tool,
        multiple_artifact_save_tool,
        artifact_list_tool,
        # 파일 처리 도구
        file_type_detector_tool,
        pdf_processor_tool,
        csv_processor_tool,
        universal_file_processor_tool
    ],
    output_key="saved_artifacts"
)
