import datetime
import uuid
from zoneinfo import ZoneInfo
from google.adk.agents import SequentialAgent, LoopAgent, Agent
from google.adk.agents.callback_context import CallbackContext

from .sub_agents.generation.report_generation_agent import report_generation_agent
from .sub_agents.evaluation.report_evaluation_agent import report_evaluation_agent
from .sub_agents.evaluation.tools.condition_checker_tool import condition_checker_tool
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


# 리포트 생성 및 평가를 순차적으로 실행하는 에이전트
report_generation_evaluation_agent = SequentialAgent(
    name="report_generation_evaluation_agent",
    description=(
        "CSV 데이터를 분석하여 리포트를 생성하고 품질을 평가합니다.\n"
        "1. 리포트 생성 에이전트를 호출하여 CSV 데이터 분석 및 리포트 생성\n"
        "2. 리포트 평가 에이전트를 호출하여 생성된 리포트의 품질 평가"
    ),
    sub_agents=[report_generation_agent, report_evaluation_agent],
)


# 체커 에이전트 - 루프 종료 조건을 확인
checker_agent = Agent(
    name="checker_agent",
    model="gemini-2.0-flash",
    description="리포트 품질과 반복 횟수를 확인하여 루프 종료 여부를 결정하는 에이전트",
    instruction=(
        f"리포트 품질 점수가 {QUALITY_THRESHOLD}점 이상이거나 "
        f"최대 반복 횟수({MAX_ITERATIONS}회)에 도달했는지 확인하세요.\n"
        "조건 확인 도구를 사용하여 루프 종료 여부를 결정하세요."
    ),
    tools=[condition_checker_tool],
    output_key="checker_output",
)


# 메인 루프 에이전트 - 품질 기준을 만족할 때까지 반복
mvp_report_generator = LoopAgent(
    name="mvp_report_generator",
    description=(
        "CSV 데이터를 분석하여 고품질 리포트를 생성합니다.\n"
        "품질 기준을 만족할 때까지 리포트 생성과 평가를 반복합니다."
    ),
    sub_agents=[
        report_generation_evaluation_agent,  # 리포트 생성 및 평가
        checker_agent,                       # 조건 확인 및 루프 종료 결정
    ],
    before_agent_callback=set_session,
)

# 루트 에이전트
root_agent = mvp_report_generator