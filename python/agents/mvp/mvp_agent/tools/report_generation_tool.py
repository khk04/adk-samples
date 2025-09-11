import json
from datetime import datetime
from pathlib import Path
from google.adk.tools import ToolContext, FunctionTool
from ..config import REPORTS_DIR


def generate_report(tool_context: ToolContext, report_content: str) -> dict:
    """
    분석된 데이터를 바탕으로 한국어 리포트를 생성합니다.
    
    Args:
        tool_context: ADK 도구 컨텍스트
        report_content: 생성할 리포트 내용
    
    Returns:
        dict: 리포트 생성 결과
    """
    try:
        # 리포트 디렉토리 생성
        reports_path = Path(REPORTS_DIR)
        reports_path.mkdir(parents=True, exist_ok=True)
        
        # 고유한 리포트 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        iteration = tool_context.state.get("loop_iteration", 1)
        report_filename = f"report_{timestamp}_iter_{iteration}.txt"
        report_path = reports_path / report_filename
        
        # 리포트 내용을 파일로 저장
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        # 리포트 정보를 세션 상태에 저장
        report_info = {
            "filename": report_filename,
            "path": str(report_path),
            "content": report_content,
            "created_at": timestamp,
            "iteration": iteration
        }
        
        tool_context.state["current_report"] = report_info
        
        return {
            "status": "success",
            "message": f"리포트 생성 완료: {report_filename}",
            "report_info": report_info
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"리포트 생성 중 오류 발생: {str(e)}"
        }


# FunctionTool로 래핑
report_generation_tool = FunctionTool(func=generate_report)