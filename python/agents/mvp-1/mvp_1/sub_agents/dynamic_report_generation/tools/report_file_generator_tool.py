"""
리포트 파일 생성 도구

분석 결과를 바탕으로 실제 리포트 파일을 생성하여 reports 디렉토리에 저장하는 도구입니다.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from google.adk.tools.function_tool import FunctionTool
import os
import json
from datetime import datetime
from pathlib import Path
from ....config import REPORTS_DIR


class ReportFileGeneratorInput(BaseModel):
    """리포트 파일 생성 입력"""
    report_title: str = Field(..., description="리포트 제목")
    report_content: str = Field(..., description="리포트 내용 (마크다운 형식)")
    output_format: str = Field(default="markdown", description="출력 형식 (markdown, html, txt)")
    user_requirements: Dict[str, Any] = Field(default_factory=dict, description="사용자 요구사항 및 선호도")
    analysis_results: Dict[str, Any] = Field(default_factory=dict, description="분석 결과 데이터")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="리포트 메타데이터")


class ReportFileGeneratorOutput(BaseModel):
    """리포트 파일 생성 출력"""
    success: bool = Field(..., description="파일 생성 성공 여부")
    file_path: str = Field(..., description="생성된 파일 경로")
    file_size: int = Field(default=0, description="파일 크기 (바이트)")
    file_format: str = Field(..., description="생성된 파일 형식")
    message: str = Field(..., description="처리 결과 메시지")
    additional_files: List[str] = Field(default_factory=list, description="추가로 생성된 파일들 (차트, 이미지 등)")


@FunctionTool
def generate_report_file(
    report_title: str,
    report_content: str,
    output_format: str = "markdown",
    user_requirements: Optional[Dict[str, Any]] = None,
    analysis_results: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> ReportFileGeneratorOutput:
    """
    분석 결과를 바탕으로 실제 리포트 파일을 생성하여 reports 디렉토리에 저장합니다.
    
    Args:
        report_title: 리포트 제목
        report_content: 리포트 내용 (마크다운 형식)
        output_format: 출력 형식 (markdown, html, txt)
        user_requirements: 사용자 요구사항 및 선호도
        analysis_results: 분석 결과 데이터
        metadata: 리포트 메타데이터
    
    Returns:
        ReportFileGeneratorOutput: 파일 생성 결과
    """
    
    if user_requirements is None:
        user_requirements = {}
    if analysis_results is None:
        analysis_results = {}
    if metadata is None:
        metadata = {}
    
    try:
        # reports 디렉토리 생성 (config.py의 REPORTS_DIR 사용)
        reports_dir = _create_reports_directory()
        
        # 파일명 생성 (타임스탬프 포함)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = _sanitize_filename(report_title)
        base_filename = f"{safe_title}_{timestamp}"
        
        # 출력 형식에 따른 파일 생성
        if output_format.lower() == "html":
            file_content = _generate_html_report(
                report_title, report_content, user_requirements, analysis_results, metadata
            )
            file_path = str(REPORTS_DIR / f"{base_filename}.html")
        elif output_format.lower() == "txt":
            file_content = _generate_text_report(
                report_title, report_content, user_requirements, analysis_results, metadata
            )
            file_path = str(REPORTS_DIR / f"{base_filename}.txt")
        else:  # 기본값: markdown
            file_content = _generate_markdown_report(
                report_title, report_content, user_requirements, analysis_results, metadata
            )
            file_path = str(REPORTS_DIR / f"{base_filename}.md")
        
        # 파일 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_content)
        
        # 파일 크기 확인
        file_size = os.path.getsize(file_path)
        
        # 메타데이터 파일 생성
        metadata_file = _generate_metadata_file(base_filename, metadata, analysis_results)
        
        additional_files = []
        if metadata_file:
            additional_files.append(metadata_file)
        
        return ReportFileGeneratorOutput(
            success=True,
            file_path=file_path,
            file_size=file_size,
            file_format=output_format.lower(),
            message=f"리포트 파일이 성공적으로 생성되었습니다: {os.path.basename(file_path)}",
            additional_files=additional_files
        )
        
    except Exception as e:
        return ReportFileGeneratorOutput(
            success=False,
            file_path="",
            file_size=0,
            file_format=output_format,
            message=f"리포트 파일 생성 중 오류가 발생했습니다: {str(e)}",
            additional_files=[]
        )


def _create_reports_directory() -> str:
    """reports 디렉토리를 생성하고 경로를 반환합니다."""
    # config.py의 REPORTS_DIR 사용
    reports_dir = str(REPORTS_DIR)
    
    # 디렉토리가 없으면 생성
    os.makedirs(reports_dir, exist_ok=True)
    
    return reports_dir


def _sanitize_filename(filename: str) -> str:
    """파일명에서 사용할 수 없는 문자를 제거합니다."""
    # 파일명에서 사용할 수 없는 문자들
    invalid_chars = '<>:"/\\|?*'
    
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # 공백을 언더스코어로 변경
    filename = filename.replace(' ', '_')
    
    # 길이 제한 (50자)
    if len(filename) > 50:
        filename = filename[:50]
    
    return filename


def _generate_markdown_report(
    title: str, 
    content: str, 
    user_requirements: Dict[str, Any], 
    analysis_results: Dict[str, Any], 
    metadata: Dict[str, Any]
) -> str:
    """마크다운 형식의 리포트를 생성합니다."""
    
    # 헤더 정보 생성
    header = f"""# {title}

**생성 일시:** {datetime.now().strftime("%Y년 %m월 %d일 %H:%M:%S")}
**분석 도메인:** {user_requirements.get('domain', '일반')}
**분석 범위:** {user_requirements.get('analysis_scope', '전체 데이터')}
**생성자:** Dynamic Report Generation Agent

---

"""
    
    # 사용자 요구사항 섹션 추가
    if user_requirements:
        header += """## 📋 사용자 요구사항

"""
        for key, value in user_requirements.items():
            header += f"- **{key}:** {value}\n"
        header += "\n---\n\n"
    
    # 원본 내용 추가
    full_content = header + content
    
    # 푸터 추가
    footer = f"""

---

**리포트 생성 정보:**
- 생성 도구: Dynamic Report Generation Agent
- 생성 시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- 데이터 소스: vdata 폴더
- 분석 도메인: {user_requirements.get('domain', '일반')}
- 저장 위치: {str(REPORTS_DIR)}

이 리포트는 사용자의 요구사항에 따라 동적으로 생성되었습니다.
"""
    
    return full_content + footer


def _generate_html_report(
    title: str, 
    content: str, 
    user_requirements: Dict[str, Any], 
    analysis_results: Dict[str, Any], 
    metadata: Dict[str, Any]
) -> str:
    """HTML 형식의 리포트를 생성합니다."""
    
    # 마크다운을 HTML로 변환하는 간단한 함수
    html_content = _markdown_to_html(content)
    
    html_report = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        h3 {{
            color: #7f8c8d;
        }}
        .metadata {{
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .highlight {{
            background-color: #fff3cd;
            padding: 10px;
            border-left: 4px solid #ffc107;
            margin: 10px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        
        <div class="metadata">
            <strong>생성 일시:</strong> {datetime.now().strftime("%Y년 %m월 %d일 %H:%M:%S")}<br>
            <strong>분석 도메인:</strong> {user_requirements.get('domain', '일반')}<br>
            <strong>분석 범위:</strong> {user_requirements.get('analysis_scope', '전체 데이터')}<br>
            <strong>생성자:</strong> Dynamic Report Generation Agent<br>
            <strong>저장 위치:</strong> {str(REPORTS_DIR)}
        </div>
        
        {html_content}
        
        <div class="footer">
            <p><strong>리포트 생성 정보:</strong></p>
            <ul>
                <li>생성 도구: Dynamic Report Generation Agent</li>
                <li>생성 시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</li>
                <li>데이터 소스: vdata 폴더</li>
                <li>분석 도메인: {user_requirements.get('domain', '일반')}</li>
                <li>저장 위치: {str(REPORTS_DIR)}</li>
            </ul>
            <p>이 리포트는 사용자의 요구사항에 따라 동적으로 생성되었습니다.</p>
        </div>
    </div>
</body>
</html>"""
    
    return html_report


def _generate_text_report(
    title: str, 
    content: str, 
    user_requirements: Dict[str, Any], 
    analysis_results: Dict[str, Any], 
    metadata: Dict[str, Any]
) -> str:
    """텍스트 형식의 리포트를 생성합니다."""
    
    # 마크다운을 텍스트로 변환
    text_content = _markdown_to_text(content)
    
    text_report = f"""{title}
{'=' * len(title)}

생성 일시: {datetime.now().strftime("%Y년 %m월 %d일 %H:%M:%S")}
분석 도메인: {user_requirements.get('domain', '일반')}
분석 범위: {user_requirements.get('analysis_scope', '전체 데이터')}
생성자: Dynamic Report Generation Agent
저장 위치: {str(REPORTS_DIR)}

{'=' * 80}

{text_content}

{'=' * 80}

리포트 생성 정보:
- 생성 도구: Dynamic Report Generation Agent
- 생성 시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- 데이터 소스: vdata 폴더
- 분석 도메인: {user_requirements.get('domain', '일반')}
- 저장 위치: {str(REPORTS_DIR)}

이 리포트는 사용자의 요구사항에 따라 동적으로 생성되었습니다.
"""
    
    return text_report


def _markdown_to_html(markdown_content: str) -> str:
    """간단한 마크다운을 HTML로 변환합니다."""
    html = markdown_content
    
    # 헤더 변환
    html = html.replace('### ', '<h3>').replace('\n# ', '\n<h1>').replace('\n## ', '\n<h2>')
    html = html.replace('\n### ', '\n<h3>')
    
    # 굵은 글씨
    html = html.replace('**', '<strong>').replace('**', '</strong>')
    
    # 기울임체
    html = html.replace('*', '<em>').replace('*', '</em>')
    
    # 줄바꿈
    html = html.replace('\n', '<br>\n')
    
    return html


def _markdown_to_text(markdown_content: str) -> str:
    """마크다운을 일반 텍스트로 변환합니다."""
    text = markdown_content
    
    # 헤더 제거
    text = text.replace('# ', '').replace('## ', '').replace('### ', '')
    
    # 마크다운 문법 제거
    text = text.replace('**', '').replace('*', '')
    text = text.replace('`', '')
    
    return text


def _generate_metadata_file(
    base_filename: str, 
    metadata: Dict[str, Any], 
    analysis_results: Dict[str, Any]
) -> Optional[str]:
    """메타데이터 파일을 생성합니다."""
    try:
        metadata_content = {
            "report_info": {
                "title": metadata.get("title", "분석 리포트"),
                "generated_at": datetime.now().isoformat(),
                "generator": "Dynamic Report Generation Agent",
                "version": "1.0",
                "storage_location": str(REPORTS_DIR)
            },
            "user_requirements": metadata.get("user_requirements", {}),
            "analysis_results": analysis_results,
            "metadata": metadata
        }
        
        metadata_file_path = str(REPORTS_DIR / f"{base_filename}_metadata.json")
        
        with open(metadata_file_path, 'w', encoding='utf-8') as f:
            json.dump(metadata_content, f, ensure_ascii=False, indent=2)
        
        return metadata_file_path
        
    except Exception as e:
        print(f"메타데이터 파일 생성 실패: {e}")
        return None


class ReportFileGeneratorTool:
    def __init__(self):
        self.name = "generate_report_file"
        self.description = "분석 결과를 바탕으로 실제 리포트 파일을 생성하여 reports 디렉토리에 저장합니다. 마크다운, HTML, 텍스트 형식을 지원합니다."
        self.input_model = ReportFileGeneratorInput
        self.output_model = ReportFileGeneratorOutput
        self.execute = generate_report_file