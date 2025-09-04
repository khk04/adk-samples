# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""ADK 기반 에이전트 클래스 정의"""

from google.adk.agents import Agent, LlmAgent
from google.adk.tools.agent_tool import AgentTool

from .prompt import (
    DOCUMENT_QUESTION_AGENT_INSTRUCTION,
    REPORT_AGENT_INSTRUCTION,
    MAIN_AGENT_INSTRUCTION
)
from .tools import (
    analyze_document,
    generate_questions,
    regenerate_questions,
    generate_report_draft,
    finalize_report,
    get_document_status,
    list_available_documents,
    export_report_to_pdf
)

# Document Question Agent
document_question_agent = Agent(
    model="gemini-2.5-flash",
    name="document_question_agent",
    instruction=DOCUMENT_QUESTION_AGENT_INSTRUCTION,
    tools=[
        analyze_document,
        generate_questions,
        regenerate_questions,
        get_document_status,
        list_available_documents
    ]
)

# Report Agent
report_agent = Agent(
    model="gemini-2.5-flash", 
    name="report_agent",
    instruction=REPORT_AGENT_INSTRUCTION,
    tools=[
        generate_report_draft,
        finalize_report,
        export_report_to_pdf,
        get_document_status
    ]
)

# Main Coordinator Agent
main_agent = LlmAgent(
    name="doc_question_report_coordinator",
    model="gemini-2.5-pro",
    description=(
        "문서 질문 및 보고서 생성 시스템의 메인 코디네이터입니다. "
        "사용자의 요청에 따라 Document Question Agent와 Report Agent를 "
        "적절히 조율하여 문서 분석, 질문 생성, 보고서 작성을 수행합니다."
    ),
    instruction=MAIN_AGENT_INSTRUCTION,
    tools=[
        AgentTool(agent=document_question_agent),
        AgentTool(agent=report_agent),
        analyze_document,
        generate_questions,
        regenerate_questions,
        generate_report_draft,
        finalize_report,
        get_document_status,
        list_available_documents,
        export_report_to_pdf
    ]
)

# Root Agent (메인 에이전트)
root_agent = main_agent