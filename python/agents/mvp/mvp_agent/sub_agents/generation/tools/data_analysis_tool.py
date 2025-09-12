import pandas as pd
import shutil
import io
from pathlib import Path
from typing import Optional, Dict, Any, Union, List
from google.adk.tools import ToolContext, FunctionTool
from ....config import SAMPLE_DATA_PATH, DATA_DIR


async def get_artifact_files(tool_context: ToolContext) -> List[Dict[str, str]]:
    """
    Artifact에 저장된 파일 목록을 가져옵니다.
    
    Args:
        tool_context: ADK 도구 컨텍스트
    
    Returns:
        List[Dict[str, str]]: 파일 정보 리스트 (filename, file_path, file_type)
    """
    try:
        print("------------------------------------------------")
        print("Artifact 파일 목록 조회 중...")
        
        # Artifact ID 목록 가져오기
        artifact_ids = await tool_context.list_artifacts()
        print(f"발견된 Artifact ID 개수: {len(artifact_ids)}")
        
        files = []
        for artifact_id in artifact_ids:
            try:
                print(f"Artifact ID {artifact_id} 처리 중...")
                
                # Artifact 내용 로드
                artifact_content = await tool_context.load_artifact(artifact_id)
                
                # 파일 정보 추출
                if hasattr(artifact_content, 'inline_data') and artifact_content.inline_data:
                    mime_type = artifact_content.inline_data.mime_type
                    display_name = artifact_content.inline_data.display_name
                    file_data = artifact_content.inline_data.data
                    
                    print(f"파일명: {display_name}")
                    print(f"MIME 타입: {mime_type}")
                    print(f"데이터 크기: {len(file_data)} bytes")
                    
                    # MIME 타입을 기반으로 파일 형식 결정
                    file_type = "unknown"
                    if mime_type == "text/csv" or display_name.endswith('.csv'):
                        file_type = "csv"
                    elif mime_type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                                     "application/vnd.ms-excel"] or display_name.endswith(('.xlsx', '.xls')):
                        file_type = "excel"
                    
                    files.append({
                        "filename": display_name,
                        "artifact_id": artifact_id,
                        "file_type": file_type,
                        "mime_type": mime_type,
                        "data_size": len(file_data),
                        "file_data": file_data
                    })
                    
            except Exception as e:
                print(f"Artifact ID {artifact_id} 처리 실패: {str(e)}")
                continue
        
        print(f"성공적으로 처리된 파일 개수: {len(files)}")
        print("------------------------------------------------")
        
        return files
        
    except Exception as e:
        print(f"Artifact 파일 목록 가져오기 실패: {str(e)}")
        return [{"error": f"Artifact 파일 목록 가져오기 실패: {str(e)}"}]


def save_artifact_file_to_data_dir(file_data: bytes, filename: str) -> str:
    """
    Artifact 파일 데이터를 data 디렉토리에 저장합니다.
    
    Args:
        file_data: Artifact에서 가져온 파일 데이터 (bytes)
        filename: 저장할 파일명
    
    Returns:
        str: 저장된 파일의 전체 경로
    """
    try:
        # data 디렉토리 생성 (없으면)
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # 저장할 파일 경로
        saved_file_path = DATA_DIR / filename
        
        # 바이트 데이터를 파일로 저장
        with open(saved_file_path, 'wb') as f:
            f.write(file_data)
        
        print(f"Artifact 파일 저장 완료: {saved_file_path}")
        return str(saved_file_path)
        
    except Exception as e:
        raise Exception(f"Artifact 파일 저장 실패: {str(e)}")


def detect_data_format(file_path: str) -> str:
    """
    파일 확장자와 내용을 기반으로 데이터 형식을 감지합니다.
    
    Args:
        file_path: 파일 경로
    
    Returns:
        str: 데이터 형식 ('csv', 'excel', 'unknown')
    """
    file_path = Path(file_path)
    extension = file_path.suffix.lower()
    
    # 확장자 기반 감지 (주요 형식만)
    if extension in ['.csv']:
        return 'csv'
    elif extension in ['.xlsx', '.xls']:
        return 'excel'
    
    # 내용 기반 감지 (CSV인지 확인)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            # CSV는 쉼표로 구분된 형태
            if ',' in first_line and not first_line.startswith(('{', '[', '<')):
                return 'csv'
    except:
        pass
    
    return 'unknown'


def parse_data_file(file_path: str, data_format: str) -> pd.DataFrame:
    """
    주요 형식의 데이터 파일을 pandas DataFrame으로 변환합니다.
    
    Args:
        file_path: 파일 경로
        data_format: 데이터 형식
    
    Returns:
        pd.DataFrame: 변환된 데이터프레임
    """
    if data_format == 'csv':
        return pd.read_csv(file_path)
    elif data_format == 'excel':
        return pd.read_excel(file_path)
    else:
        raise ValueError(f"지원하지 않는 데이터 형식: {data_format}. CSV 또는 Excel 파일을 사용하세요.")


async def analyze_data(tool_context: ToolContext, file_path: Optional[str] = None) -> dict:
    """
    CSV와 Excel 형식의 데이터를 분석하고 통계 정보를 반환합니다.
    Artifact에 파일이 있으면 우선적으로 사용합니다.
    
    Args:
        tool_context: ADK 도구 컨텍스트
        file_path: 데이터 파일 경로 (없으면 Artifact 또는 샘플 데이터 사용)
    
    Returns:
        dict: 분석된 데이터 통계 정보
    """
    try:
        # 파일 경로 설정 (우선순위: file_path > Artifact > 샘플 데이터)
        if file_path is None:
            # Artifact에서 파일 목록 가져오기
            artifact_files = await get_artifact_files(tool_context)
            
            if artifact_files and not any("error" in file for file in artifact_files):
                # Artifact에서 지원하는 형식의 파일 찾기
                for file_info in artifact_files:
                    if file_info.get("file_type") in ["csv", "excel"]:
                        # Artifact 파일을 data 디렉토리에 저장
                        try:
                            saved_file_path = save_artifact_file_to_data_dir(
                                file_info["file_data"], 
                                file_info["filename"]
                            )
                            file_path = saved_file_path
                            tool_context.state["current_file_info"] = {
                                "filename": file_info["filename"],
                                "file_type": file_info["file_type"],
                                "mime_type": file_info["mime_type"],
                                "artifact_id": file_info["artifact_id"],
                                "saved_path": saved_file_path,
                                "source": "artifact"
                            }
                            break
                        except Exception as e:
                            print(f"Artifact 파일 저장 실패: {e}")
                            continue
                
                # 지원하는 파일이 없으면 샘플 데이터 사용
                if file_path is None:
                    file_path = str(SAMPLE_DATA_PATH)
                    tool_context.state["current_file_info"] = {
                        "filename": "sample_sales_data.csv",
                        "file_path": str(SAMPLE_DATA_PATH),
                        "file_type": "csv",
                        "source": "sample_data"
                    }
            else:
                # Artifact가 없거나 오류가 있으면 샘플 데이터 사용
                file_path = str(SAMPLE_DATA_PATH)
                tool_context.state["current_file_info"] = {
                    "filename": "sample_sales_data.csv",
                    "file_path": str(SAMPLE_DATA_PATH),
                    "file_type": "csv",
                    "source": "sample_data"
                }
        
        # 데이터 형식 감지
        data_format = detect_data_format(file_path)
        
        # 데이터 로드
        df = parse_data_file(file_path, data_format)
        
        # 기본 통계 정보
        total_records = len(df)
        columns = list(df.columns)
        
        # 숫자형 컬럼 식별
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
        
        # 분석 결과 초기화
        analysis_result = {
            "data_format": data_format,
            "total_records": total_records,
            "columns": columns,
            "numeric_columns": numeric_columns,
            "data_types": df.dtypes.to_dict(),
            "basic_stats": {},
            "categorical_analysis": {},
            "temporal_analysis": {},
            "correlation_analysis": {}
        }
        
        # 숫자형 컬럼 기본 통계
        if numeric_columns:
            analysis_result["basic_stats"] = df[numeric_columns].describe().round(2).to_dict()
            
            # 총합이 있는 컬럼들 찾기 (매출, 판매량 등)
            sum_columns = [col for col in numeric_columns if any(keyword in col.lower() for keyword in ['총', 'total', 'sum', 'amount', 'revenue', 'sales'])]
            if sum_columns:
                for col in sum_columns:
                    analysis_result[f"{col}_total"] = int(df[col].sum())
                    analysis_result[f"{col}_average"] = float(df[col].mean())
        
        # 카테고리형 컬럼 분석
        categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
        for col in categorical_columns:
            if df[col].nunique() < 50:  # 너무 많은 고유값이 아닌 경우만
                analysis_result["categorical_analysis"][col] = {
                    "unique_count": df[col].nunique(),
                    "value_counts": df[col].value_counts().head(10).to_dict(),
                    "top_value": df[col].mode().iloc[0] if not df[col].mode().empty else None
                }
        
        # 날짜형 컬럼 분석
        date_columns = []
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    pd.to_datetime(df[col].head(10))
                    date_columns.append(col)
                except:
                    pass
        
        if date_columns:
            for col in date_columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                if not df[col].isna().all():
                    analysis_result["temporal_analysis"][col] = {
                        "date_range": {
                            "start": str(df[col].min()),
                            "end": str(df[col].max())
                        },
                        "monthly_trend": df.groupby(df[col].dt.to_period('M')).size().to_dict()
                    }
        
        # 상관관계 분석 (숫자형 컬럼이 2개 이상인 경우)
        if len(numeric_columns) >= 2:
            correlation_matrix = df[numeric_columns].corr()
            analysis_result["correlation_analysis"] = correlation_matrix.round(3).to_dict()
        
        # 그룹별 분석 (가능한 경우)
        group_columns = [col for col in categorical_columns if df[col].nunique() < 20]
        if group_columns and numeric_columns:
            for group_col in group_columns[:3]:  # 최대 3개 그룹 컬럼만
                group_analysis = df.groupby(group_col)[numeric_columns].agg(['sum', 'mean', 'count']).round(2)
                analysis_result[f"{group_col}_analysis"] = group_analysis.to_dict()
        
        # 분석 결과를 세션 상태에 저장
        tool_context.state["data_analysis"] = analysis_result
        
        # 현재 파일 정보 가져오기
        current_file_info = tool_context.state.get("current_file_info", {})
        
        return {
            "status": "success",
            "message": f"{data_format.upper()} 데이터 분석 완료. 총 {total_records}개 레코드, {len(columns)}개 컬럼",
            "data": analysis_result,
            "file_info": {
                "filename": current_file_info.get("filename", "unknown"),
                "file_type": data_format,
                "source": current_file_info.get("source", "unknown"),
                "saved_path": current_file_info.get("saved_path", file_path)
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"데이터 분석 중 오류 발생: {str(e)}"
        }


# FunctionTool로 래핑
data_analysis_tool = FunctionTool(func=analyze_data)
artifact_files_tool = FunctionTool(func=get_artifact_files)