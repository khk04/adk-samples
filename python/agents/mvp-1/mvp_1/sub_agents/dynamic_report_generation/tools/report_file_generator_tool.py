"""
리포트 파일 생성 도구

분석 결과를 바탕으로 실제 리포트 파일을 생성하여 reports 디렉토리에 저장하는 도구입니다.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from google.adk.tools.function_tool import FunctionTool
import os
import json
import shutil
import base64
from datetime import datetime
from pathlib import Path
from ....config import REPORTS_DIR
from .visualization_generator_tool import VisualizationGeneratorTool
from .image_utils import copy_chart_images, get_chart_image_path


class ReportFileGeneratorInput(BaseModel):
    """리포트 파일 생성 입력"""
    report_title: str = Field(..., description="리포트 제목")
    report_content: str = Field(..., description="리포트 내용 (마크다운 형식)")
    output_format: str = Field(default="markdown", description="출력 형식 (markdown, html, txt)")
    user_requirements: Dict[str, Any] = Field(default_factory=dict, description="사용자 요구사항 및 선호도")
    analysis_results: Dict[str, Any] = Field(default_factory=dict, description="분석 결과 데이터")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="리포트 메타데이터")
    data_file_path: str = Field(default="", description="분석할 데이터 파일 경로")
    include_visualizations: bool = Field(default=True, description="시각화 요소 포함 여부")


class ReportFileGeneratorOutput(BaseModel):
    """리포트 파일 생성 출력"""
    success: bool = Field(..., description="파일 생성 성공 여부")
    file_path: str = Field(..., description="생성된 파일 경로")
    file_size: int = Field(default=0, description="파일 크기 (바이트)")
    file_format: str = Field(..., description="생성된 파일 형식")
    message: str = Field(..., description="처리 결과 메시지")
    additional_files: List[str] = Field(default_factory=list, description="추가로 생성된 파일들 (차트, 이미지 등)")
    visualizations: List[Dict[str, Any]] = Field(default_factory=list, description="생성된 시각화 요소들")
    charts_data: Dict[str, Any] = Field(default_factory=dict, description="차트 데이터")
    tables_data: Dict[str, Any] = Field(default_factory=dict, description="테이블 데이터")


def generate_report_file(
    report_title: str,
    report_content: str,
    output_format: str = "markdown",
    user_requirements: Optional[Dict[str, Any]] = None,
    analysis_results: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    data_file_path: str = "",
    include_visualizations: bool = True
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
        # 시각화 요소 생성 (옵션)
        visualizations = []
        charts_data = {}
        tables_data = {}
        chart_image_files = []  # 차트 이미지 파일 경로 초기화
        additional_files = []  # 추가 파일 목록 초기화
        
        # data_file_path가 없으면 자동으로 설정
        if not data_file_path:
            # user_requirements에서 데이터 파일 경로 추출 시도
            data_file_path = user_requirements.get('data_file_path', '') if user_requirements else ''
            
            # 여전히 없으면 기본 vdata 디렉토리에서 파일 찾기
            if not data_file_path:
                vdata_dir = Path("/Users/khk/work/connev/adk-samples/python/agents/mvp-1/data/vdata")
                if vdata_dir.exists():
                    csv_files = list(vdata_dir.glob("*.csv"))
                    if csv_files:
                        data_file_path = str(csv_files[0])  # 첫 번째 CSV 파일 사용
                        print(f"자동으로 데이터 파일 설정: {data_file_path}")
        
        # 리포트별 디렉토리 생성 (시각화 생성 전에 먼저 생성)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = _sanitize_filename(report_title)
        report_dir_name = f"{safe_title}_{timestamp}"
        report_dir = REPORTS_DIR / report_dir_name
        
        # 리포트 디렉토리 및 하위 디렉토리 생성
        report_dir.mkdir(parents=True, exist_ok=True)
        charts_dir = report_dir / "charts"
        charts_dir.mkdir(exist_ok=True)
        data_dir = report_dir / "data"
        data_dir.mkdir(exist_ok=True)
        
        print(f"리포트 디렉토리 생성: {report_dir}")
        
        # 시각화 생성 조건 확인 및 로깅
        print(f"시각화 생성 조건 확인:")
        print(f"  - include_visualizations: {include_visualizations}")
        print(f"  - data_file_path: {data_file_path}")
        print(f"  - output_format: {output_format}")
        
        if include_visualizations and data_file_path:
            try:
                print(f"시각화 생성 시작: {data_file_path}")
                # VisualizationGeneratorTool의 execute는 FunctionTool이므로 직접 호출
                from .visualization_generator_tool import generate_dynamic_visualizations
                domain_type = user_requirements.get('domain', '일반')
                analysis_purpose = user_requirements.get('analysis_purpose', '일반 분석')
                
                print(f"시각화 도구 호출 파라미터:")
                print(f"  - domain_type: {domain_type}")
                print(f"  - analysis_purpose: {analysis_purpose}")
                print(f"  - output_format: {output_format}")
                print(f"  - target_dir: {str(charts_dir)}")
                
                viz_result = generate_dynamic_visualizations(
                    data_file_path=data_file_path,
                    domain_type=domain_type,
                    analysis_purpose=analysis_purpose,
                    analysis_results=analysis_results,
                    visualization_requirements={},
                    output_format=output_format,
                    target_dir=str(charts_dir)
                )
                
                if viz_result.success:
                    visualizations = viz_result.visualizations
                    charts_data = viz_result.charts_data
                    tables_data = viz_result.tables_data
                    additional_files.extend(viz_result.generated_files)
                    
                    # 차트 이미지 파일들을 additional_files에 추가
                    chart_images = viz_result.generated_files
                    print(f"시각화 도구에서 생성된 이미지 파일들: {chart_images}")
                    
                    # 차트 이미지 파일 경로를 로컬 변수로 저장
                    chart_image_files = [f for f in chart_images if f.endswith('.png')]
                    print(f"차트 이미지 파일 경로: {chart_image_files}")
                else:
                    # 시각화 생성 실패 시에도 기본 데이터는 생성
                    print(f"시각화 생성 실패 (기본 데이터로 계속): {viz_result.message}")
                    # 차트 이미지 파일 경로 초기화
                    chart_image_files = []
                    # 기본 테이블 데이터 생성
                    try:
                        import pandas as pd
                        df = pd.read_csv(data_file_path)
                        tables_data = {
                            'data_summary': {
                                'total_rows': len(df),
                                'total_columns': len(df.columns),
                                'numeric_columns': len(df.select_dtypes(include=['number']).columns),
                                'categorical_columns': len(df.select_dtypes(include=['object']).columns)
                            }
                        }
                    except:
                        pass
            except Exception as e:
                print(f"시각화 생성 중 오류 (무시하고 계속): {e}")
                # 오류 발생 시에도 변수 초기화
                chart_image_files = []
        else:
            print(f"시각화 생성 조건 미충족:")
            print(f"  - include_visualizations: {include_visualizations}")
            print(f"  - data_file_path: {data_file_path}")
            if not include_visualizations:
                print("  → include_visualizations가 False입니다.")
            if not data_file_path:
                print("  → data_file_path가 비어있습니다.")
        
        # 리포트별 디렉토리는 이미 위에서 생성됨
        
        # 출력 형식에 따른 파일 생성 (시각화 요소 포함)
        if output_format.lower() == "html":
            file_content = _generate_html_report(
                report_title, report_content, user_requirements, analysis_results, metadata, visualizations, charts_data, tables_data, chart_image_files, charts_dir
            )
            file_path = str(report_dir / "index.html")
            
            # HTML 파일의 경우 차트 이미지 파일들을 charts 디렉토리로 복사
            if chart_image_files:
                copy_chart_images(chart_image_files, charts_dir, use_standard_names=True)
                print(f"차트 이미지 파일들 복사 완료: {chart_image_files}")
        elif output_format.lower() == "txt":
            file_content = _generate_text_report(
                report_title, report_content, user_requirements, analysis_results, metadata, visualizations, charts_data, tables_data
            )
            file_path = str(report_dir / "report.txt")
        else:  # 기본값: markdown
            file_content = _generate_markdown_report(
                report_title, report_content, user_requirements, analysis_results, metadata, visualizations, charts_data, tables_data
            )
            file_path = str(report_dir / "report.md")
        
        # 파일 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_content)
        
        # 파일 크기 확인
        file_size = os.path.getsize(file_path)
        
        # 메타데이터 파일 생성 (data 디렉토리에 저장)
        metadata_file = _generate_metadata_file(report_dir_name, metadata, analysis_results, additional_files, data_dir)
        
        if metadata_file:
            additional_files.append(metadata_file)
        
        return ReportFileGeneratorOutput(
            success=True,
            file_path=file_path,
            file_size=file_size,
            file_format=output_format.lower(),
            message=f"리포트 파일이 성공적으로 생성되었습니다: {os.path.basename(file_path)}",
            additional_files=additional_files,
            visualizations=visualizations,
            charts_data=charts_data,
            tables_data=tables_data
        )
        
    except Exception as e:
        return ReportFileGeneratorOutput(
            success=False,
            file_path="",
            file_size=0,
            file_format=output_format,
            message=f"리포트 파일 생성 중 오류가 발생했습니다: {str(e)}",
            additional_files=[],
            visualizations=[],
            charts_data={},
            tables_data={}
        )


def _create_reports_directory() -> str:
    """reports 디렉토리를 생성하고 경로를 반환합니다."""
    # config.py의 REPORTS_DIR 사용
    reports_dir = str(REPORTS_DIR)
    
    # 디렉토리가 없으면 생성
    os.makedirs(reports_dir, exist_ok=True)
    
    return reports_dir


# _copy_chart_images_to_charts_dir 함수는 image_utils.py의 copy_chart_images로 대체됨

def _copy_chart_images_to_reports_dir(chart_image_files: List[str], reports_dir: Path) -> None:
    """차트 이미지 파일들을 reports 디렉토리로 복사합니다. (기존 호환성 유지)"""
    try:
        print(f"차트 이미지 복사 시작: {len(chart_image_files)}개 파일")
        for image_file in chart_image_files:
            if os.path.exists(image_file):
                # 파일명만 추출
                filename = os.path.basename(image_file)
                destination = reports_dir / filename
                
                # 파일이 이미 존재하지 않는 경우에만 복사
                if not destination.exists():
                    shutil.copy2(image_file, destination)
                    print(f"차트 이미지 복사 완료: {image_file} -> {destination}")
                else:
                    print(f"차트 이미지 이미 존재: {destination}")
            else:
                print(f"차트 이미지 파일이 존재하지 않음: {image_file}")
        print(f"차트 이미지 복사 완료: {len(chart_image_files)}개 파일 처리")
    except Exception as e:
        print(f"차트 이미지 복사 중 오류: {e}")


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
    metadata: Dict[str, Any],
    visualizations: List[Dict[str, Any]] = None,
    charts_data: Dict[str, Any] = None,
    tables_data: Dict[str, Any] = None
) -> str:
    """마크다운 형식의 리포트를 생성합니다."""
    
    if visualizations is None:
        visualizations = []
    if charts_data is None:
        charts_data = {}
    if tables_data is None:
        tables_data = {}
    
    # 사용자 친화적 헤더 정보 생성
    current_time = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
    domain = user_requirements.get('domain', '일반')
    analysis_scope = user_requirements.get('analysis_scope', '전체 데이터')
    
    header = f"""# {title}

> **분석 완료일:** {current_time}  
> **분석 영역:** {domain}  
> **분석 범위:** {analysis_scope}  
> **시각화:** {len(visualizations)}개 차트 포함

---

## **이 리포트로 무엇을 할 수 있나요?**

**즉시 활용 가능한 인사이트** - 데이터에서 발견된 핵심 패턴과 트렌드  
**실행 가능한 권장사항** - 구체적인 개선 방안과 실행 계획  
**시각적 분석 결과** - 이해하기 쉬운 차트와 그래프  
**비즈니스 의사결정 지원** - 데이터 기반의 객관적 근거  

---

"""
    
    # 사용자 요구사항 섹션 추가 (더 친화적으로)
    if user_requirements:
        header += """## **분석 요청사항 요약**

"""
        # 사용자 친화적인 키 매핑
        friendly_keys = {
            'domain': '분석 영역',
            'analysis_scope': '분석 범위', 
            'analysis_criteria': '분석 기준',
            'filtering_conditions': '필터링 조건',
            'analysis_style': '분석 스타일',
            'detail_level': '상세 수준',
            'output_format': '결과 형식'
        }
        
        for key, value in user_requirements.items():
            friendly_key = friendly_keys.get(key, key)
            header += f"• **{friendly_key}:** {value}\n"
        header += "\n---\n\n"
    
    # 원본 내용 추가
    full_content = header + content
    
    # 시각화 요소 추가 (더 친화적으로)
    if visualizations:
        full_content += "\n## **시각화 분석 결과**\n\n"
        full_content += "> **아래 차트들을 통해 데이터의 패턴과 트렌드를 시각적으로 확인할 수 있습니다.**\n\n"
        
        for i, viz in enumerate(visualizations, 1):
            full_content += f"### {i}. {viz['title']}\n"
            full_content += f"**차트 유형:** {viz['type']} | **분석 목적:** {viz.get('chart_type', '일반 분석')}\n"
            full_content += f"**설명:** {viz['description']}\n\n"
    
    # 차트 데이터 요약 추가 (더 친화적으로)
    if charts_data:
        full_content += "\n## **주요 차트 데이터 요약**\n\n"
        full_content += "> **아래는 생성된 차트들의 핵심 데이터 요약입니다.**\n\n"
        for key, value in charts_data.items():
            if isinstance(value, dict):
                full_content += f"### {key}\n"
                for sub_key, sub_value in value.items():
                    full_content += f"• **{sub_key}:** {sub_value}\n"
                full_content += "\n"
    
    # 테이블 데이터 요약 추가 (더 친화적으로)
    if tables_data:
        full_content += "\n## **데이터 테이블 요약**\n\n"
        full_content += "> **아래는 분석에 사용된 주요 테이블 데이터 요약입니다.**\n\n"
        for key, value in tables_data.items():
            if isinstance(value, dict):
                full_content += f"### {key}\n"
                if 'total_rows' in value:
                    full_content += f"• **총 데이터 건수:** {value['total_rows']:,}개\n"
                if 'total_columns' in value:
                    full_content += f"• **분석 컬럼 수:** {value['total_columns']}개\n"
                
                # 상위 성과자 테이블
                if 'top_performers' in value and isinstance(value['top_performers'], list):
                    full_content += f"• **상위 성과자:** {len(value['top_performers'])}명\n"
                
                full_content += "\n"
    
    # 사용자 친화적 푸터 추가
    footer = f"""

---

## **리포트 생성 완료!**

> **생성 완료:** {datetime.now().strftime("%Y년 %m월 %d일 %H:%M")}  
> **저장 위치:** data/reports/ 폴더  
> **다음 단계:** 위의 인사이트와 권장사항을 검토하고 실행 계획을 수립해보세요!

### **이 리포트를 어떻게 활용하시겠어요?**

1. **팀과 공유** - 핵심 인사이트를 팀원들과 논의
2. **실행 계획 수립** - 권장사항 중 우선순위 높은 항목부터 실행
3. **정기 모니터링** - 데이터 업데이트 후 트렌드 변화 추적
4. **추가 분석** - 궁금한 부분에 대한 심화 분석 요청

### **리포트 구성 정보**
- **분석 영역:** {user_requirements.get('domain', '일반')}
- **시각화 요소:** {len(visualizations)}개 차트 포함
- **데이터 섹션:** {len(charts_data)}개 차트 데이터, {len(tables_data)}개 테이블 데이터

> **궁금한 점이 있으시거나 추가 분석이 필요하시면 언제든 말씀해 주세요!**
"""
    
    return full_content + footer


def _generate_html_report(
    title: str, 
    content: str, 
    user_requirements: Dict[str, Any], 
    analysis_results: Dict[str, Any], 
    metadata: Dict[str, Any],
    visualizations: List[Dict[str, Any]] = None,
    charts_data: Dict[str, Any] = None,
    tables_data: Dict[str, Any] = None,
    chart_image_files: List[str] = None,
    charts_dir: Path = None
) -> str:
    """HTML 형식의 리포트를 생성합니다."""
    
    if visualizations is None:
        visualizations = []
    if charts_data is None:
        charts_data = {}
    if tables_data is None:
        tables_data = {}
    if chart_image_files is None:
        chart_image_files = []
    
    # 마크다운을 HTML로 변환하는 간단한 함수 (차트 이미지 파일명 매핑 포함)
    html_content = _markdown_to_html(content, chart_image_files, charts_dir)
    
    # 시각화 요소 HTML 생성 (더 친화적으로)
    viz_html = ""
    if visualizations:
        viz_html = """
        <h2><strong>시각화 분석 결과</strong></h2>
        <div class="info-box">
            <p><strong>아래 차트들을 통해 데이터의 패턴과 트렌드를 시각적으로 확인할 수 있습니다.</strong></p>
        </div>
        """
        
        # 파라미터로 전달받은 차트 이미지 파일 경로 사용
        print(f"HTML 생성 시 사용할 차트 이미지 파일들: {chart_image_files}")
        
        for i, viz in enumerate(visualizations, 1):
            # 실제 생성된 차트 이미지 파일 경로 사용
            chart_image_src = ""
            chart_image_name = "N/A"
            
            if i-1 < len(chart_image_files) and chart_image_files[i-1]:
                chart_image_path = Path(chart_image_files[i-1])
                chart_image_name = chart_image_path.name
                
                # 새로운 디렉토리 구조에 맞게 이미지 경로 설정
                if charts_dir:
                    # 공통 함수 사용
                    chart_image_src = get_chart_image_path(i-1, charts_dir, use_standard_names=True)
                    chart_image_name = f"chart_{i-1}.png"
                    print(f"차트 {i} 새로운 디렉토리 구조 사용: {chart_image_src}")
                else:
                    # 기존 방식 (하위 호환성)
                    try:
                        if chart_image_path.exists():
                            # 상대 경로 사용 (HTML 파일과 같은 디렉토리에 있으므로)
                            chart_image_src = chart_image_name
                            print(f"차트 {i} 이미지 상대 경로 사용: {chart_image_src}")
                        else:
                            # 파일이 없으면 절대 경로로 시도
                            chart_image_src = f"file://{chart_image_path.absolute()}"
                            print(f"차트 {i} 이미지 파일 없음, 절대 경로 사용: {chart_image_src}")
                    except Exception as e:
                        # 파일 경로 설정 실패 시 기본값 사용
                        chart_image_src = chart_image_name
                        print(f"차트 {i} 파일 경로 설정 실패, 기본값 사용: {e}")
            else:
                # 기본 패턴
                if charts_dir:
                    chart_image_src = get_chart_image_path(i-1, charts_dir, use_standard_names=True)
                    chart_image_name = f"chart_{i-1}.png"
                    print(f"차트 {i} 기본 새로운 디렉토리 구조 사용: {chart_image_src}")
                else:
                    chart_image_src = f"chart_{i-1}.png"
                    chart_image_name = f"chart_{i-1}.png"
                    print(f"차트 {i} 기본 상대 경로 사용: {chart_image_src}")
            
            viz_html += f"""
            <div class="visualization-item">
                <h3>{i}. {viz['title']}</h3>
                <p><strong>차트 유형:</strong> {viz['type']} | <strong>분석 목적:</strong> {viz.get('chart_type', '일반 분석')}</p>
                <p><strong>설명:</strong> {viz['description']}</p>
                <div class="chart-container">
                    <img src="{chart_image_src}" alt="{viz['title']}" style="max-width: 600px; width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px;" onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                    <p class="chart-note" style="display: none; color: #e74c3c; font-style: italic;">차트 이미지를 로드할 수 없습니다: {chart_image_src}<br>파일 경로를 확인해주세요.</p>
                    <p class="chart-note">{viz['title']} - {viz['type']} 차트<br>이미지 파일: {chart_image_name}</p>
                </div>
            </div>
            """
    
    # 차트 데이터 HTML 생성
    charts_html = ""
    if charts_data:
        charts_html = "<h2>주요 차트 데이터</h2>"
        for key, value in charts_data.items():
            if isinstance(value, dict):
                charts_html += f"<h3>{key}</h3><ul>"
                for sub_key, sub_value in value.items():
                    charts_html += f"<li><strong>{sub_key}:</strong> {sub_value}</li>"
                charts_html += "</ul>"
    
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
        .visualization-item {{
            margin: 30px 0;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }}
        .chart-container {{
            margin: 15px 0;
            text-align: center;
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .chart-note {{
            margin-top: 10px;
            font-size: 0.9em;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        
        <div class="metadata">
            <h3>이 리포트로 무엇을 할 수 있나요?</h3>
            <div class="highlight">
                <p><strong>즉시 활용 가능한 인사이트</strong> - 데이터에서 발견된 핵심 패턴과 트렌드</p>
                <p><strong>실행 가능한 권장사항</strong> - 구체적인 개선 방안과 실행 계획</p>
                <p><strong>시각적 분석 결과</strong> - 이해하기 쉬운 차트와 그래프</p>
                <p><strong>비즈니스 의사결정 지원</strong> - 데이터 기반의 객관적 근거</p>
            </div>
            <p><strong>분석 완료일:</strong> {datetime.now().strftime("%Y년 %m월 %d일 %H:%M")}</p>
            <p><strong>분석 영역:</strong> {user_requirements.get('domain', '일반')}</p>
            <p><strong>분석 범위:</strong> {user_requirements.get('analysis_scope', '전체 데이터')}</p>
            <p><strong>시각화:</strong> {len(visualizations)}개 차트 포함</p>
        </div>
        
        {html_content}
        
        {viz_html}
        
        {charts_html}
        
        <div class="footer">
            <h2><strong>리포트 생성 완료!</strong></h2>
            <div class="highlight">
                <p><strong>생성 완료:</strong> {datetime.now().strftime("%Y년 %m월 %d일 %H:%M")}</p>
                <p><strong>저장 위치:</strong> data/reports/ 폴더</p>
                <p><strong>다음 단계:</strong> 위의 인사이트와 권장사항을 검토하고 실행 계획을 수립해보세요!</p>
            </div>
            
            <h3><strong>이 리포트를 어떻게 활용하시겠어요?</strong></h3>
            <ol>
                <li><strong>팀과 공유</strong> - 핵심 인사이트를 팀원들과 논의</li>
                <li><strong>실행 계획 수립</strong> - 권장사항 중 우선순위 높은 항목부터 실행</li>
                <li><strong>정기 모니터링</strong> - 데이터 업데이트 후 트렌드 변화 추적</li>
                <li><strong>추가 분석</strong> - 궁금한 부분에 대한 심화 분석 요청</li>
            </ol>
            
            <h3><strong>리포트 구성 정보</strong></h3>
            <ul>
                <li><strong>분석 영역:</strong> {user_requirements.get('domain', '일반')}</li>
                <li><strong>시각화 요소:</strong> {len(visualizations)}개 차트 포함</li>
                <li><strong>데이터 섹션:</strong> {len(charts_data)}개 차트 데이터, {len(tables_data)}개 테이블 데이터</li>
            </ul>
            
            <div class="highlight">
                <p><strong>궁금한 점이 있으시거나 추가 분석이 필요하시면 언제든 말씀해 주세요!</strong></p>
            </div>
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
    metadata: Dict[str, Any],
    visualizations: List[Dict[str, Any]] = None,
    charts_data: Dict[str, Any] = None,
    tables_data: Dict[str, Any] = None
) -> str:
    """텍스트 형식의 리포트를 생성합니다."""
    
    if visualizations is None:
        visualizations = []
    if charts_data is None:
        charts_data = {}
    if tables_data is None:
        tables_data = {}
    
    # 마크다운을 텍스트로 변환
    text_content = _markdown_to_text(content)
    
    # 시각화 요소 텍스트 추가 (더 친화적으로)
    viz_text = ""
    if visualizations:
        viz_text = "\n\n=== 시각화 분석 결과 ===\n"
        viz_text += "아래 차트들을 통해 데이터의 패턴과 트렌드를 시각적으로 확인할 수 있습니다.\n\n"
        for i, viz in enumerate(visualizations, 1):
            viz_text += f"{i}. {viz['title']}\n"
            viz_text += f"   차트 유형: {viz['type']} | 분석 목적: {viz.get('chart_type', '일반 분석')}\n"
            viz_text += f"   설명: {viz['description']}\n\n"
    
    # 차트 데이터 텍스트 추가
    charts_text = ""
    if charts_data:
        charts_text = "\n\n=== 주요 차트 데이터 ===\n"
        for key, value in charts_data.items():
            if isinstance(value, dict):
                charts_text += f"{key}:\n"
                for sub_key, sub_value in value.items():
                    charts_text += f"  - {sub_key}: {sub_value}\n"
                charts_text += "\n"
    
    text_report = f"""{title}
{'=' * (len(title) + 2)}

이 리포트로 무엇을 할 수 있나요?
- 즉시 활용 가능한 인사이트 - 데이터에서 발견된 핵심 패턴과 트렌드
- 실행 가능한 권장사항 - 구체적인 개선 방안과 실행 계획
- 시각적 분석 결과 - 이해하기 쉬운 차트와 그래프
- 비즈니스 의사결정 지원 - 데이터 기반의 객관적 근거

분석 완료일: {datetime.now().strftime("%Y년 %m월 %d일 %H:%M")}
분석 영역: {user_requirements.get('domain', '일반')}
분석 범위: {user_requirements.get('analysis_scope', '전체 데이터')}
시각화: {len(visualizations)}개 차트 포함

{'=' * 80}

{text_content}
{viz_text}
{charts_text}
{'=' * 80}

리포트 생성 완료!

생성 완료: {datetime.now().strftime("%Y년 %m월 %d일 %H:%M")}
저장 위치: data/reports/ 폴더
다음 단계: 위의 인사이트와 권장사항을 검토하고 실행 계획을 수립해보세요!

이 리포트를 어떻게 활용하시겠어요?
1. 팀과 공유 - 핵심 인사이트를 팀원들과 논의
2. 실행 계획 수립 - 권장사항 중 우선순위 높은 항목부터 실행
3. 정기 모니터링 - 데이터 업데이트 후 트렌드 변화 추적
4. 추가 분석 - 궁금한 부분에 대한 심화 분석 요청

리포트 구성 정보
- 분석 영역: {user_requirements.get('domain', '일반')}
- 시각화 요소: {len(visualizations)}개 차트 포함
- 데이터 섹션: {len(charts_data)}개 차트 데이터, {len(tables_data)}개 테이블 데이터

궁금한 점이 있으시거나 추가 분석이 필요하시면 언제든 말씀해 주세요!
"""
    
    return text_report


def _markdown_to_html(markdown_content: str, chart_image_files: List[str] = None, charts_dir: Path = None) -> str:
    """간단한 마크다운을 HTML로 변환합니다."""
    html = markdown_content
    
    # 차트 이미지 파일명 매핑 (새로운 디렉토리 구조에 맞게)
    if chart_image_files and charts_dir:
        for i, image_file in enumerate(chart_image_files):
            if i < 5:  # 최대 5개 차트만 처리
                # 공통 함수 사용
                charts_path = get_chart_image_path(i, charts_dir, use_standard_names=True)
                
                # 다양한 패턴 매핑 (하드코딩된 패턴들)
                patterns_to_replace = [
                    f"./chart_{i+1}.png",
                    f"chart_{i+1}.png", 
                    f"./chart_{i}.png",
                    f"chart_{i}.png"
                ]
                for old_pattern in patterns_to_replace:
                    if old_pattern in html:
                        html = html.replace(old_pattern, charts_path)
                        print(f"이미지 경로 매핑: {old_pattern} -> {charts_path}")
    elif chart_image_files:
        # 기존 방식 (하위 호환성)
        for i, image_file in enumerate(chart_image_files):
            if i < 5:  # 최대 5개 차트만 처리
                actual_filename = Path(image_file).name
                # 다양한 패턴 매핑 (하드코딩된 패턴들)
                patterns_to_replace = [
                    f"./chart_{i+1}.png",
                    f"chart_{i+1}.png", 
                    f"./chart_{i}.png",
                    f"chart_{i}.png"
                ]
                for old_pattern in patterns_to_replace:
                    if old_pattern in html:
                        html = html.replace(old_pattern, actual_filename)
                        print(f"이미지 경로 매핑: {old_pattern} -> {actual_filename}")
    
    # 헤더 변환 (닫는 태그 추가)
    html = html.replace('\n# ', '\n<h1>').replace('\n## ', '\n<h2>').replace('\n### ', '\n<h3>')
    html = html.replace('\n<h1>', '\n<h1>').replace('\n<h2>', '\n<h2>').replace('\n<h3>', '\n<h3>')
    
    # 헤더 닫는 태그 추가 (줄바꿈 전에)
    html = html.replace('<h1>', '<h1>').replace('<h2>', '<h2>').replace('<h3>', '<h3>')
    html = html.replace('<h1><br>', '<h1>').replace('<h2><br>', '<h2>').replace('<h3><br>', '<h3>')
    html = html.replace('<h1>', '<h1>').replace('<h2>', '<h2>').replace('<h3>', '<h3>')
    
    # 굵은 글씨 변환 (더 정확한 방법)
    import re
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    
    # 기울임체 변환 (더 정확한 방법)
    html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
    
    # 줄바꿈
    html = html.replace('\n', '<br>\n')
    
    # 헤더 닫는 태그 추가
    html = re.sub(r'<h1>(.*?)<br>', r'<h1>\1</h1><br>', html)
    html = re.sub(r'<h2>(.*?)<br>', r'<h2>\1</h2><br>', html)
    html = re.sub(r'<h3>(.*?)<br>', r'<h3>\1</h3><br>', html)
    
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
    report_dir_name: str, 
    metadata: Dict[str, Any], 
    analysis_results: Dict[str, Any],
    generated_files: List[str] = None,
    data_dir: Path = None
) -> Optional[str]:
    """메타데이터 파일을 생성합니다."""
    try:
        metadata_content = {
            "report_info": {
                "title": metadata.get("title", "분석 리포트"),
                "generated_at": datetime.now().isoformat(),
                "generator": "Dynamic Report Generation Agent",
                "version": "2.0",
                "storage_location": str(REPORTS_DIR),
                "report_directory": report_dir_name,
                "directory_structure": {
                    "index_file": "index.html",
                    "charts_directory": "charts/",
                    "data_directory": "data/",
                    "assets_directory": "assets/"
                }
            },
            "user_requirements": metadata.get("user_requirements", {}),
            "analysis_results": analysis_results,
            "metadata": metadata,
            "generated_files": generated_files or [],
            "chart_files": [f"chart_{i}.png" for i in range(5)]  # 표준화된 차트 파일명
        }
        
        if data_dir:
            metadata_file_path = str(data_dir / "metadata.json")
        else:
            metadata_file_path = str(REPORTS_DIR / f"{report_dir_name}_metadata.json")
        
        with open(metadata_file_path, 'w', encoding='utf-8') as f:
            json.dump(metadata_content, f, ensure_ascii=False, indent=2)
        
        return metadata_file_path
        
    except Exception as e:
        print(f"메타데이터 파일 생성 실패: {e}")
        return None


class ReportFileGeneratorTool:
    def __init__(self):
        self.name = "generate_report_file"
        self.description = "분석 결과를 바탕으로 실제 리포트 파일을 생성하여 reports 디렉토리에 저장합니다. 마크다운, HTML(실제 차트 이미지 포함), 텍스트 형식을 지원합니다."
        self.input_model = ReportFileGeneratorInput
        self.output_model = ReportFileGeneratorOutput
        self.execute = generate_report_file