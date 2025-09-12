import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from google.adk.tools import ToolContext, FunctionTool
from ....config import DATA_DIR, REPORTS_DIR


def read_saved_artifact_file(tool_context: ToolContext, filename: str) -> dict:
    """
    저장된 아티팩트 파일을 읽어옵니다.
    
    Args:
        tool_context: ADK 도구 컨텍스트
        filename: 읽을 파일명
    
    Returns:
        dict: 파일 내용 및 정보
    """
    try:
        # data 디렉토리에서 파일 찾기
        data_path = Path(DATA_DIR)
        file_path = data_path / filename
        
        if not file_path.exists():
            return {
                "status": "error",
                "message": f"파일을 찾을 수 없습니다: {filename}"
            }
        
        # 파일 내용 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 파일 정보
        file_info = {
            "filename": filename,
            "path": str(file_path),
            "size": os.path.getsize(file_path),
            "content": content
        }
        
        return {
            "status": "success",
            "message": f"파일 읽기 완료: {filename}",
            "file_info": file_info
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"파일 읽기 중 오류 발생: {str(e)}"
        }


def list_available_files(tool_context: ToolContext, directory: str = "data") -> dict:
    """
    사용 가능한 파일 목록을 조회합니다.
    
    Args:
        tool_context: ADK 도구 컨텍스트
        directory: 조회할 디렉토리 ("data" 또는 "reports")
    
    Returns:
        dict: 파일 목록
    """
    try:
        if directory == "data":
            target_path = Path(DATA_DIR)
        elif directory == "reports":
            target_path = Path(REPORTS_DIR)
        else:
            return {
                "status": "error",
                "message": "지원하지 않는 디렉토리입니다. 'data' 또는 'reports'를 사용하세요."
            }
        
        if not target_path.exists():
            return {
                "status": "success",
                "message": f"{directory} 디렉토리가 존재하지 않습니다.",
                "files": []
            }
        
        # 파일 목록 가져오기
        files = []
        for file_path in target_path.iterdir():
            if file_path.is_file():
                files.append({
                    "filename": file_path.name,
                    "path": str(file_path),
                    "size": os.path.getsize(file_path),
                    "extension": file_path.suffix
                })
        
        # 파일명으로 정렬
        files.sort(key=lambda x: x["filename"])
        
        return {
            "status": "success",
            "message": f"{directory} 디렉토리에서 {len(files)}개 파일 발견",
            "files": files
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"파일 목록 조회 중 오류 발생: {str(e)}"
        }


def read_latest_artifact_file(tool_context: ToolContext) -> dict:
    """
    가장 최근에 저장된 아티팩트 파일을 읽어옵니다.
    
    Args:
        tool_context: ADK 도구 컨텍스트
    
    Returns:
        dict: 최신 파일 내용 및 정보
    """
    try:
        # 저장된 아티팩트 목록에서 최신 파일 찾기
        saved_artifacts = tool_context.state.get("saved_artifacts", [])
        
        if not saved_artifacts:
            return {
                "status": "error",
                "message": "저장된 아티팩트가 없습니다."
            }
        
        # 가장 최근 파일 선택 (created_at 기준)
        latest_artifact = max(saved_artifacts, key=lambda x: x.get("created_at", ""))
        filename = latest_artifact["filename"]
        
        # 파일 읽기
        return read_saved_artifact_file(tool_context, filename)
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"최신 아티팩트 파일 읽기 중 오류 발생: {str(e)}"
        }


def read_artifact_by_iteration(tool_context: ToolContext, iteration: int) -> dict:
    """
    특정 반복 횟수에 저장된 아티팩트 파일을 읽어옵니다.
    
    Args:
        tool_context: ADK 도구 컨텍스트
        iteration: 반복 횟수
    
    Returns:
        dict: 해당 반복의 파일 내용 및 정보
    """
    try:
        # 저장된 아티팩트 목록에서 해당 반복 파일 찾기
        saved_artifacts = tool_context.state.get("saved_artifacts", [])
        
        target_artifact = None
        for artifact in saved_artifacts:
            if artifact.get("iteration") == iteration:
                target_artifact = artifact
                break
        
        if not target_artifact:
            return {
                "status": "error",
                "message": f"반복 {iteration}에 저장된 아티팩트를 찾을 수 없습니다."
            }
        
        filename = target_artifact["filename"]
        
        # 파일 읽기
        return read_saved_artifact_file(tool_context, filename)
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"반복 {iteration} 아티팩트 파일 읽기 중 오류 발생: {str(e)}"
        }


# FunctionTool로 래핑
file_reader_tool = FunctionTool(func=read_saved_artifact_file)
file_list_tool = FunctionTool(func=list_available_files)
latest_artifact_tool = FunctionTool(func=read_latest_artifact_file)
iteration_artifact_tool = FunctionTool(func=read_artifact_by_iteration)