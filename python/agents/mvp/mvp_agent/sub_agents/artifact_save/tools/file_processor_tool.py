import io
import pandas as pd
from typing import Optional, Dict, Any
from google.adk.tools import ToolContext, FunctionTool
from pypdf import PdfReader
import pdfplumber


class PdfReaderError(Exception):
    pass


def detect_file_type(tool_context: ToolContext, file_content: str, filename: Optional[str] = None) -> dict:
    """
    파일 내용과 이름을 기반으로 파일 타입을 감지합니다.
    
    Args:
        tool_context: ADK 도구 컨텍스트
        file_content: 파일 내용
        filename: 파일명 (선택사항)
    
    Returns:
        dict: 파일 타입 감지 결과
    """
    try:
        detected_type = "unknown"
        confidence = 0.0
        
        # 파일명 기반 감지
        if filename:
            filename_lower = filename.lower()
            if filename_lower.endswith('.pdf'):
                detected_type = "pdf"
                confidence = 0.9
            elif filename_lower.endswith(('.csv', '.tsv')):
                detected_type = "csv"
                confidence = 0.9
            elif filename_lower.endswith(('.xlsx', '.xls')):
                detected_type = "excel"
                confidence = 0.9
        
        # 내용 기반 감지
        if confidence < 0.8:
            content_lower = file_content.lower()
            
            # PDF 시그니처 확인
            if file_content.startswith('%PDF-'):
                detected_type = "pdf"
                confidence = 0.95
            # CSV 패턴 확인 (쉼표로 구분된 데이터)
            elif ',' in file_content and '\n' in file_content:
                lines = file_content.split('\n')[:5]
                if all(',' in line for line in lines if line.strip()):
                    detected_type = "csv"
                    confidence = 0.85
        
        return {
            "status": "success",
            "detected_type": detected_type,
            "confidence": confidence,
            "filename": filename
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"파일 타입 감지 중 오류 발생: {str(e)}"
        }


def process_pdf_file(tool_context: ToolContext, pdf_content: str) -> dict:
    """
    PDF 파일을 처리하고 텍스트를 추출합니다.
    
    Args:
        tool_context: ADK 도구 컨텍스트
        pdf_content: PDF 파일의 바이트 내용
    
    Returns:
        dict: PDF 처리 결과
    """
    try:
        # PDF 바이트 스트림 생성
        if isinstance(pdf_content, str):
            pdf_bytes = pdf_content.encode('utf-8')
        else:
            pdf_bytes = pdf_content
            
        pdf_bytes_stream = io.BytesIO(pdf_bytes)
        
        # PDF 유효성 검사
        try:
            reader = PdfReader(pdf_bytes_stream)
            if not reader.pages:
                raise PdfReaderError("PDF에 페이지가 없습니다.")
        except Exception as e:
            raise PdfReaderError(f"PDF를 안전하게 구문 분석하지 못했습니다: {e}")
        
        # 텍스트 추출
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            full_text = ""
            page_count = len(pdf.pages)
            
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    full_text += f"=== 페이지 {page_num + 1} ===\n"
                    full_text += page_text + "\n\n"
        
        # 추출된 텍스트를 세션 상태에 저장
        tool_context.state["extracted_pdf_text"] = full_text
        tool_context.state["pdf_page_count"] = page_count
        
        return {
            "status": "success",
            "message": f"PDF 처리 완료: {page_count}페이지, {len(full_text)}자 텍스트 추출",
            "page_count": page_count,
            "text_length": len(full_text),
            "text_preview": full_text[:500] + "..." if len(full_text) > 500 else full_text
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"PDF 처리 중 오류 발생: {str(e)}"
        }


def process_csv_file(tool_context: ToolContext, csv_content: str) -> dict:
    """
    CSV 파일을 처리하고 분석합니다.
    
    Args:
        tool_context: ADK 도구 컨텍스트
        csv_content: CSV 파일의 내용
    
    Returns:
        dict: CSV 처리 결과
    """
    try:
        # CSV 내용을 DataFrame으로 변환
        csv_io = io.StringIO(csv_content)
        df = pd.read_csv(csv_io)
        
        # 기본 정보 수집
        total_rows = len(df)
        total_columns = len(df.columns)
        column_names = list(df.columns)
        
        # 숫자형 컬럼 식별
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
        
        # 기본 통계 정보
        basic_stats = {}
        if numeric_columns:
            basic_stats = df[numeric_columns].describe().round(2).to_dict()
        
        # 카테고리형 컬럼 분석
        categorical_analysis = {}
        categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
        for col in categorical_columns:
            if df[col].nunique() < 50:  # 너무 많은 고유값이 아닌 경우만
                categorical_analysis[col] = {
                    "unique_count": df[col].nunique(),
                    "value_counts": df[col].value_counts().head(10).to_dict(),
                    "top_value": df[col].mode().iloc[0] if not df[col].mode().empty else None
                }
        
        # 처리 결과를 세션 상태에 저장
        csv_analysis = {
            "total_rows": total_rows,
            "total_columns": total_columns,
            "column_names": column_names,
            "numeric_columns": numeric_columns,
            "basic_stats": basic_stats,
            "categorical_analysis": categorical_analysis,
            "data_preview": df.head(5).to_dict('records')
        }
        
        tool_context.state["csv_analysis"] = csv_analysis
        tool_context.state["csv_dataframe"] = df.to_json(orient='records')
        
        return {
            "status": "success",
            "message": f"CSV 처리 완료: {total_rows}행, {total_columns}열",
            "analysis": csv_analysis
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"CSV 처리 중 오류 발생: {str(e)}"
        }


def process_any_file(tool_context: ToolContext, file_content: str, filename: Optional[str] = None) -> dict:
    """
    파일 타입을 자동 감지하고 적절한 처리기를 사용하여 파일을 처리합니다.
    
    Args:
        tool_context: ADK 도구 컨텍스트
        file_content: 파일 내용
        filename: 파일명 (선택사항)
    
    Returns:
        dict: 파일 처리 결과
    """
    try:
        # 파일 타입 감지
        type_result = detect_file_type(tool_context, file_content, filename)
        
        if type_result["status"] != "success":
            return type_result
        
        detected_type = type_result["detected_type"]
        
        # 파일 타입에 따른 처리
        if detected_type == "pdf":
            return process_pdf_file(tool_context, file_content)
        elif detected_type == "csv":
            return process_csv_file(tool_context, file_content)
        else:
            return {
                "status": "error",
                "message": f"지원하지 않는 파일 타입: {detected_type}. PDF 또는 CSV 파일을 사용하세요."
            }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"파일 처리 중 오류 발생: {str(e)}"
        }


# FunctionTool로 래핑
file_type_detector_tool = FunctionTool(func=detect_file_type)
pdf_processor_tool = FunctionTool(func=process_pdf_file)
csv_processor_tool = FunctionTool(func=process_csv_file)
universal_file_processor_tool = FunctionTool(func=process_any_file)
