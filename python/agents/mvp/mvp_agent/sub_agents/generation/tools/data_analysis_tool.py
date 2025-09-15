import pandas as pd
import shutil
import io
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any, Union, List, Tuple
from google.adk.tools import ToolContext, FunctionTool
from ....config import SAMPLE_DATA_PATH, DATA_DIR
import pdfplumber
from pypdf import PdfReader

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def save_artifact_file(tool_context: ToolContext, save_path: Optional[str] = None) -> str:
    """
    업로드된 아티팩트 파일을 로컬 시스템에 저장합니다.
    Args:
        tool_context: 상태를 포함하는 ADK 프레임워크에서 제공하는 컨텍스트 객체.
        save_path: 파일을 저장할 경로 (선택사항). 지정하지 않으면 기본 경로 사용.
    Returns:
        저장 완료 메시지와 파일 경로.
    """
    print("------------------------------------------------")
    print("아티팩트 파일 저장을 시작합니다...")
    
    try:
        # 아티팩트 목록 가져오기
        artifact_ids = await tool_context.list_artifacts()
        
        if not artifact_ids:
            return "저장할 아티팩트가 없습니다."
        
        # 첫 번째 아티팩트 사용
        artifact_id = artifact_ids[0]
        print(f"아티팩트 ID로 읽는 중: {artifact_id}")
        
        # 아티팩트 내용 로드
        artifact_content = await tool_context.load_artifact(artifact_id)
        
        # 파일 정보 추출
        file_name = artifact_content.inline_data.display_name
        file_data = artifact_content.inline_data.data
        mime_type = artifact_content.inline_data.mime_type
        
        print(f"파일명: {file_name}")
        print(f"파일 타입: {mime_type}")
        print(f"파일 크기: {len(file_data)} bytes")
        
        # 저장 경로 결정
        if save_path is None:
            # 기본 저장 디렉토리 생성 (절대 경로 사용)
            save_dir = str(DATA_DIR)
            os.makedirs(save_dir, exist_ok=True)
            
            # 원본 파일명 그대로 사용
            save_path = os.path.join(save_dir, file_name)
        else:
            # 사용자가 지정한 경로 사용
            save_dir = os.path.dirname(save_path)
            if save_dir:
                os.makedirs(save_dir, exist_ok=True)
        
        # 파일 저장
        with open(save_path, 'wb') as f:
            f.write(file_data)
        
        print(f"파일이 성공적으로 저장되었습니다: {save_path}")
        print("------------------------------------------------")
        
        return f"아티팩트 파일이 성공적으로 저장되었습니다.\n저장 경로: {save_path}\n파일명: {file_name}\n파일 타입: {mime_type}\n파일 크기: {len(file_data)} bytes"
        
    except Exception as e:
        error_msg = f"파일 저장 중 오류가 발생했습니다: {e}"
        print(error_msg)
        print("------------------------------------------------")
        return error_msg


def detect_data_format(file_path: str) -> str:
    """파일 확장자를 기반으로 데이터 형식을 감지합니다."""
    file_path = Path(file_path)
    extension = file_path.suffix.lower()
    
    if extension == '.csv':
        return 'csv'
    elif extension in ['.xlsx', '.xls']:
        return 'excel'
    elif extension == '.pdf':
        return 'pdf'
    else:
        return 'unknown'


def parse_data_file(file_path: str, data_format: str) -> pd.DataFrame:
    """파일을 읽어서 pandas DataFrame으로 변환합니다."""
    try:
        if data_format == 'csv':
            return pd.read_csv(file_path, encoding='utf-8')
        elif data_format == 'excel':
            return pd.read_excel(file_path)
        elif data_format == 'pdf':
            return _parse_pdf_file(file_path)
        else:
            raise ValueError(f"지원하지 않는 데이터 형식: {data_format}")
    except Exception as e:
        logger.error(f"데이터 파일 파싱 실패: {e}")
        raise


def _parse_pdf_file(file_path: str) -> pd.DataFrame:
    """PDF 파일에서 텍스트를 추출하여 DataFrame으로 변환합니다."""
    try:
        with pdfplumber.open(file_path) as pdf:
            pages_data = []
            
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    pages_data.append({
                        'page': page_num,
                        'text': text,
                        'text_length': len(text)
                    })
            
            if not pages_data:
                return pd.DataFrame(columns=['page', 'text', 'text_length'])
            
            return pd.DataFrame(pages_data)
            
    except Exception as e:
        logger.error(f"PDF 파일 파싱 실패: {e}")
        raise


def analyze_dataframe(df: pd.DataFrame, file_type: str = None) -> Dict[str, Any]:
    """DataFrame을 분석하여 통계 정보를 반환합니다."""
    try:
        # 기본 통계
        basic_stats = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "memory_usage": df.memory_usage(deep=True).sum(),
            "dtypes": df.dtypes.astype(str).to_dict()
        }
        
        # 누락 데이터 분석
        missing_data = df.isnull().sum().to_dict()
        
        # 상관관계 분석 (수치형 컬럼만)
        numeric_columns = df.select_dtypes(include=['number']).columns
        correlation_analysis = {}
        if len(numeric_columns) > 1:
            correlation_matrix = df[numeric_columns].corr()
            correlation_analysis = correlation_matrix.to_dict()
        
        # PDF 특별 분석
        pdf_analysis = {}
        if file_type == 'pdf':
            pdf_analysis = _analyze_pdf_data(df)
        
        # 결과 반환
        result = {
            "basic_stats": _convert_pandas_to_json_safe(basic_stats),
            "missing_data": _convert_pandas_to_json_safe(missing_data),
            "correlation_analysis": _convert_pandas_to_json_safe(correlation_analysis),
            "pdf_analysis": pdf_analysis
        }
        
        return result
        
    except Exception as e:
        logger.error(f"DataFrame 분석 실패: {e}")
        raise


def _analyze_pdf_data(df: pd.DataFrame) -> Dict[str, Any]:
    """PDF 데이터를 분석합니다."""
    try:
        if 'text' not in df.columns:
            return {"error": "PDF 텍스트 데이터가 없습니다."}
        
        # 전체 텍스트 통계
        total_text = ' '.join(df['text'].fillna(''))
        total_chars = len(total_text)
        total_words = len(total_text.split())
        
        # 페이지별 통계
        page_stats = []
        for _, row in df.iterrows():
            page_text = str(row.get('text', ''))
            page_stats.append({
                'page': int(row.get('page', 0)),
                'characters': len(page_text),
                'words': len(page_text.split())
            })
        
        # 키워드 빈도 (간단한 분석)
        words = total_text.lower().split()
        word_freq = {}
        for word in words:
            if len(word) > 3:  # 3글자 이상만
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 상위 10개 키워드
        top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_pages": len(df),
            "total_characters": total_chars,
            "total_words": total_words,
            "page_stats": page_stats,
            "top_keywords": top_keywords
        }
        
    except Exception as e:
        logger.error(f"PDF 데이터 분석 실패: {e}")
        return {"error": f"PDF 분석 실패: {str(e)}"}


def _convert_pandas_to_json_safe(data: Any) -> Any:
    """pandas 객체를 JSON 직렬화 가능한 형태로 변환"""
    if isinstance(data, dict):
        return {str(k): _convert_pandas_to_json_safe(v) for k, v in data.items()}
    elif isinstance(data, (list, tuple)):
        return [_convert_pandas_to_json_safe(item) for item in data]
    elif hasattr(data, 'item'):  # numpy scalar
        return data.item()
    elif hasattr(data, 'tolist'):  # numpy array
        return data.tolist()
    else:
        return str(data) if data is not None else None


async def analyze_data(tool_context: ToolContext, file_path: Optional[str] = None) -> str:
    """
    데이터 파일을 분석하여 통계 정보를 반환합니다.
    
    Args:
        tool_context: ADK 프레임워크에서 제공하는 컨텍스트 객체
        file_path: 분석할 파일 경로 (선택사항)
    
    Returns:
        str: 분석 결과 JSON 문자열
    """
    try:
        logger.info("=== 데이터 분석 시작 ===")
        
        # 파일 경로 결정
        final_file_path, file_info = await _determine_file_path(tool_context, file_path)
        logger.info(f"분석할 파일: {final_file_path}")
        
        # 데이터 형식 감지
        data_format = detect_data_format(final_file_path)
        logger.info(f"감지된 데이터 형식: {data_format}")
        
        if data_format == 'unknown':
            return f"지원하지 않는 데이터 형식입니다: {final_file_path}"
        
        # 데이터 파싱
        df = parse_data_file(final_file_path, data_format)
        logger.info(f"데이터 로드 완료: {len(df)}행, {len(df.columns)}열")
        
        # 데이터 분석
        analysis_result = analyze_dataframe(df, data_format)
        
        # 파일 정보 추가
        analysis_result["file_info"] = file_info
        
        logger.info("=== 데이터 분석 완료 ===")
        return str(analysis_result)
        
    except Exception as e:
        error_msg = f"데이터 분석 중 오류 발생: {str(e)}"
        logger.error(error_msg)
        return error_msg


async def _determine_file_path(tool_context: ToolContext, file_path: Optional[str]) -> Tuple[str, Dict[str, Any]]:
    """파일 경로를 결정하고 파일 정보를 반환"""
    
    if file_path is not None:
        # 명시적으로 지정된 파일 경로 사용
        return file_path, {
            "filename": Path(file_path).name,
            "file_path": file_path,
            "source": "explicit"
        }
    
    # 무한 루프 방지: 이미 Artifact 처리를 시도했는지 확인
    if "artifact_processing_attempted" in tool_context.state:
        logger.info("이미 Artifact 처리를 시도했습니다. 샘플 데이터를 사용합니다.")
        return str(SAMPLE_DATA_PATH), {
            "filename": "sample_sales_data.csv",
            "file_path": str(SAMPLE_DATA_PATH),
            "file_type": "csv",
            "source": "sample_data"
        }
    
    # 새로운 PDF 처리 로직으로 Artifact 파일 처리
    logger.info("=== 새로운 PDF 처리 로직으로 Artifact 파일 처리 시작 ===")
    tool_context.state["artifact_processing_attempted"] = True
    
    try:
        # 1. Artifact 목록 조회
        artifact_ids = await tool_context.list_artifacts()
        logger.info(f"발견된 Artifact ID 개수: {len(artifact_ids)}")
        
        if not artifact_ids:
            logger.info("업로드된 문서가 없습니다.")
            raise Exception("업로드된 문서가 없습니다.")
        
        # 첫 번째 Artifact 사용
        artifact_id = artifact_ids[0]
        logger.info(f"처리할 Artifact ID: {artifact_id}")
        
        # 2. Artifact 내용 로드
        try:
            artifact_data = await tool_context.load_artifact(artifact_id)
            logger.info(f"Artifact 로드 성공: {len(artifact_data)} bytes")
        except Exception as e:
            logger.error(f"Artifact 로드 실패: {e}")
            raise Exception(f"Artifact 로드 실패: {e}")
        
        # 3. 파일명 추출 (Artifact ID 기반)
        filename = f"artifact_{artifact_id}.pdf"
        logger.info(f"추출된 파일명: {filename}")
        
        # 4. PDF 유효성 검사
        try:
            # pypdf로 PDF 유효성 검사
            pdf_reader = PdfReader(io.BytesIO(artifact_data))
            page_count = len(pdf_reader.pages)
            logger.info(f"PDF 유효성 검사 성공: {page_count}페이지")
            
            # pdfplumber로 추가 검증
            with pdfplumber.open(io.BytesIO(artifact_data)) as pdf:
                total_pages = len(pdf.pages)
                logger.info(f"pdfplumber 검증 성공: {total_pages}페이지")
                
        except Exception as e:
            logger.error(f"PDF 유효성 검사 실패: {e}")
            raise Exception(f"PDF 유효성 검사 실패: {e}")
        
        # 5. 파일 저장
        try:
            logger.info(f"파일 저장 시도: {filename} (크기: {len(artifact_data)} bytes)")
            
            # 직접 파일 저장 (절대 경로 사용)
            save_dir = str(DATA_DIR)
            os.makedirs(save_dir, exist_ok=True)
            full_save_path = os.path.join(save_dir, filename)
            
            with open(full_save_path, 'wb') as f:
                f.write(artifact_data)
            
            logger.info(f"파일이 성공적으로 저장되었습니다: {full_save_path}")
            
            # 저장된 파일이 실제로 존재하는지 확인
            if not Path(full_save_path).exists():
                logger.error(f"저장된 파일이 존재하지 않음: {full_save_path}")
                raise Exception(f"저장된 파일이 존재하지 않음: {full_save_path}")
            
            logger.info(f"=== Artifact 파일 저장 성공 ===")
            return full_save_path, {
                "filename": filename,
                "file_type": "pdf",
                "mime_type": "application/pdf",
                "artifact_id": artifact_id,
                "saved_path": full_save_path,
                "source": "artifact",
                "page_count": page_count
            }
            
        except Exception as e:
            logger.error(f"Artifact 파일 저장 실패: {e}")
            import traceback
            logger.error(f"상세 에러: {traceback.format_exc()}")
            raise Exception(f"Artifact 파일 저장 실패: {e}")
            
    except Exception as e:
        logger.error(f"새로운 PDF 처리 로직에서 예외 발생: {e}")
        import traceback
        logger.error(f"상세 에러: {traceback.format_exc()}")
    
    # 샘플 데이터 사용
    logger.info("샘플 데이터 사용")
    return str(SAMPLE_DATA_PATH), {
        "filename": "sample_sales_data.csv",
        "file_path": str(SAMPLE_DATA_PATH),
        "file_type": "csv",
        "source": "sample_data"
    }


async def get_artifact_files(tool_context: ToolContext) -> List[Dict[str, Any]]:
    """Artifact 파일 목록 가져오기 (기존 호환성 유지)"""
    try:
        artifact_ids = await tool_context.list_artifacts()
        files = []
        
        for artifact_id in artifact_ids:
            try:
                artifact_data = await tool_context.load_artifact(artifact_id)
                file_info = {
                    "artifact_id": artifact_id,
                    "filename": artifact_data.inline_data.display_name,
                    "mime_type": artifact_data.inline_data.mime_type,
                    "size": len(artifact_data.inline_data.data)
                }
                files.append(file_info)
            except Exception as e:
                logger.error(f"Artifact {artifact_id} 처리 실패: {e}")
                continue
        
        return files
    except Exception as e:
        logger.error(f"Artifact 파일 목록 조회 실패: {e}")
        return []


# FunctionTool로 래핑
data_analysis_tool = FunctionTool(func=analyze_data)
artifact_files_tool = FunctionTool(func=get_artifact_files)
save_artifact_tool = FunctionTool(func=save_artifact_file)