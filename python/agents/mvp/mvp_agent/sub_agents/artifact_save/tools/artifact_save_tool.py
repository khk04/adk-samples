import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from google.adk.tools import ToolContext, FunctionTool
from ....config import DATA_DIR


def save_artifact_to_file(tool_context: ToolContext, artifact_content: str, filename: Optional[str] = None, file_extension: str = "txt") -> dict:
    """
    아티팩트 내용을 파일로 저장합니다.
    
    Args:
        tool_context: ADK 도구 컨텍스트
        artifact_content: 저장할 아티팩트 내용
        filename: 파일명 (없으면 자동 생성)
        file_extension: 파일 확장자 (기본값: txt)
    
    Returns:
        dict: 파일 저장 결과
    """
    try:
        # 데이터 디렉토리 생성
        data_path = Path(DATA_DIR)
        data_path.mkdir(parents=True, exist_ok=True)
        
        # 파일명 생성
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            iteration = tool_context.state.get("loop_iteration", 1)
            filename = f"artifact_{timestamp}_iter_{iteration}.{file_extension}"
        
        # 확장자가 없으면 추가
        if not filename.endswith(f".{file_extension}"):
            filename = f"{filename}.{file_extension}"
        
        file_path = data_path / filename
        
        # 파일 내용 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(artifact_content)
        
        # 파일 정보를 세션 상태에 저장
        file_info = {
            "filename": filename,
            "path": str(file_path),
            "size": os.path.getsize(file_path),
            "created_at": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "iteration": tool_context.state.get("loop_iteration", 1)
        }
        
        # 저장된 파일 목록을 상태에 추가
        if "saved_artifacts" not in tool_context.state:
            tool_context.state["saved_artifacts"] = []
        tool_context.state["saved_artifacts"].append(file_info)
        
        return {
            "status": "success",
            "message": f"아티팩트 저장 완료: {filename}",
            "file_info": file_info
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"아티팩트 저장 중 오류 발생: {str(e)}"
        }


def save_multiple_artifacts(tool_context: ToolContext, artifacts: List[Dict[str, Any]]) -> dict:
    """
    여러 아티팩트를 한 번에 파일로 저장합니다.
    
    Args:
        tool_context: ADK 도구 컨텍스트
        artifacts: 저장할 아티팩트 목록 [{"content": "내용", "filename": "파일명", "extension": "확장자"}]
    
    Returns:
        dict: 파일 저장 결과
    """
    try:
        saved_files = []
        failed_files = []
        
        for artifact in artifacts:
            content = artifact.get("content", "")
            filename = artifact.get("filename")
            extension = artifact.get("extension", "txt")
            
            if not content:
                failed_files.append({"filename": filename, "error": "내용이 비어있음"})
                continue
            
            result = save_artifact_to_file(tool_context, content, filename, extension)
            
            if result["status"] == "success":
                saved_files.append(result["file_info"])
            else:
                failed_files.append({"filename": filename, "error": result["message"]})
        
        return {
            "status": "success" if not failed_files else "partial",
            "message": f"총 {len(artifacts)}개 중 {len(saved_files)}개 저장 완료",
            "saved_files": saved_files,
            "failed_files": failed_files
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"다중 아티팩트 저장 중 오류 발생: {str(e)}"
        }


def list_saved_artifacts(tool_context: ToolContext) -> dict:
    """
    저장된 아티팩트 파일 목록을 조회합니다.
    
    Args:
        tool_context: ADK 도구 컨텍스트
    
    Returns:
        dict: 저장된 파일 목록
    """
    try:
        saved_artifacts = tool_context.state.get("saved_artifacts", [])
        
        return {
            "status": "success",
            "message": f"총 {len(saved_artifacts)}개의 저장된 아티팩트",
            "artifacts": saved_artifacts
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"아티팩트 목록 조회 중 오류 발생: {str(e)}"
        }


# FunctionTool로 래핑
artifact_save_tool = FunctionTool(func=save_artifact_to_file)
multiple_artifact_save_tool = FunctionTool(func=save_multiple_artifacts)
artifact_list_tool = FunctionTool(func=list_saved_artifacts)
