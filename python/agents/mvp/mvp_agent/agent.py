import datetime
import uuid
from zoneinfo import ZoneInfo
from google.adk.agents import SequentialAgent, LoopAgent, Agent
from google.adk.agents.callback_context import CallbackContext

from .sub_agents.generation.report_generation_agent import data_analysis_report_agent
from .sub_agents.artifact_save.artifact_save_agent import artifact_save_agent
from .sub_agents.evaluation.report_evaluation_agent import report_evaluation_agent
from .sub_agents.evaluation.tools.condition_checker_tool import condition_checker_tool
from .prompt import get_checker_prompt
from .config import QUALITY_THRESHOLD, MAX_ITERATIONS


def set_session(callback_context: CallbackContext):
    """
    세션 초기화 - 고유 ID와 타임스탬프를 설정합니다.
    """
    callback_context.state["unique_id"] = str(uuid.uuid4())
    callback_context.state["timestamp"] = datetime.datetime.now(
        ZoneInfo("Asia/Seoul")
    ).isoformat()
    callback_context.state["loop_iteration"] = 0


# 아티팩트 저장, 데이터 분석, 리포트 생성, 평가를 순차적으로 실행하는 에이전트
data_analysis_report_evaluation_agent = SequentialAgent(
    name="data_analysis_report_evaluation_agent",
    description=(
        "파일을 분석하여 리포트를 생성하고 품질을 평가합니다.\n"
        "1. artifact_save_agent로 사용자 파일을 아티팩트로 저장\n"
        "2. data_analysis_report_agent 호출하여 데이터 분석 및 리포트 생성\n"
        "3. 리포트 평가 에이전트를 호출하여 생성된 리포트의 품질 평가\n"
        "지원 형식: CSV, Excel"
    ),
    sub_agents=[artifact_save_agent, data_analysis_report_agent, report_evaluation_agent],
)


# 체커 에이전트 - 루프 종료 조건을 확인
checker_agent = Agent(
    name="checker_agent",
    model="gemini-2.0-flash",
    description="리포트 품질과 반복 횟수를 확인하여 루프 종료 여부를 결정하는 에이전트",
    instruction=get_checker_prompt(QUALITY_THRESHOLD, MAX_ITERATIONS),
    tools=[condition_checker_tool],
    output_key="checker_output",
)


# 메인 루프 에이전트 - 품질 기준을 만족할 때까지 반복
data_report_generator = LoopAgent(
    name="data_report_generator",
    description=(
        "사용자 데이터를 기반으로 고품질 리포트를 생성합니다.\n"
        "품질 기준을 만족할 때까지 데이터 분석, 리포트 생성과 평가를 반복합니다."
        "만약 분석할 데이터가 없으면 작업을 종료합니다."
    ),
    sub_agents=[
        data_analysis_report_evaluation_agent,  # 데이터 분석, 리포트 생성 및 평가
        checker_agent,                          # 조건 확인 및 루프 종료 결정
    ],
    before_agent_callback=set_session,
)

# 루트 에이전트
root_agent = data_report_generator