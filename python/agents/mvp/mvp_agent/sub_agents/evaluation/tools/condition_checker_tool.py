from google.adk.tools import ToolContext, FunctionTool
from ....config import QUALITY_THRESHOLD, MAX_ITERATIONS


def check_condition_and_escalate(tool_context: ToolContext) -> dict:
    """
    루프 종료 조건을 확인하고 필요시 에스컬레이션합니다.
    
    Args:
        tool_context: ADK 도구 컨텍스트
    
    Returns:
        dict: 조건 확인 결과
    """
    try:
        # 현재 반복 횟수 증가
        current_iteration = tool_context.state.get("loop_iteration", 0)
        current_iteration += 1
        tool_context.state["loop_iteration"] = current_iteration
        
        # 리포트 평가 결과 가져오기
        evaluation = tool_context.state.get("report_evaluation")
        if not evaluation:
            return {
                "status": "error",
                "message": "평가 결과가 없습니다."
            }
        
        total_score = evaluation.get("total_score", 0)
        
        # 조건 확인
        quality_met = total_score >= QUALITY_THRESHOLD
        max_iterations_reached = current_iteration >= MAX_ITERATIONS
        
        response_message = f"반복 {current_iteration}회: 품질 점수 {total_score:.2f}/10, 임계값 {QUALITY_THRESHOLD}"
        
        # 종료 조건 확인
        if quality_met:
            tool_context.actions.escalate = True
            response_message += f" - 품질 기준 충족, 루프 종료"
        elif max_iterations_reached:
            tool_context.actions.escalate = True
            response_message += f" - 최대 반복 횟수({MAX_ITERATIONS}) 도달, 루프 종료"
        else:
            response_message += f" - 기준 미충족, 루프 계속"
        
        return {
            "status": "success",
            "message": response_message,
            "current_iteration": current_iteration,
            "total_score": total_score,
            "quality_threshold": QUALITY_THRESHOLD,
            "quality_met": quality_met,
            "max_iterations_reached": max_iterations_reached
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"조건 확인 중 오류 발생: {str(e)}"
        }


# FunctionTool로 래핑
condition_checker_tool = FunctionTool(func=check_condition_and_escalate)