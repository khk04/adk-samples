import io
from typing import Optional
from google.adk.tools import ToolContext, FunctionTool
from pypdf import PdfReader
import pdfplumber


class PdfReaderError(Exception):
    pass


async def check_uploaded_document(tool_context: ToolContext) -> str:
    """
    지정된 문서가 업로드되어 세션 상태에서 사용할 수 있는지 확인합니다.
    
    Args:
        tool_context: ADK 프레임워크가 제공하는 컨텍스트 객체로, 상태를 포함합니다.
    
    Returns:
        확인 메시지.
    """
    print("------------------------------------------------")
    artifact_ids = await tool_context.artifact_list()

    # 사용자가 업로드한 문서인 목록에서 첫 번째 아티팩트 ID를 가져옵니다.
    artifact_id = artifact_ids[0]
    print(f"ID가 {artifact_id}인 아티팩트 읽기")

    # 2. 아티팩트의 내용을 읽어보세요
    # 코루틴이 데이터를 가져올 때까지 기다립니다.
    try:
        artifact_content = await tool_context.artifact_load(artifact_id)
        print("문서 유형: ", artifact_content.inline_data.mime_type)
        file_name = artifact_content.inline_data.display_name
        pdf_bytes = artifact_content.inline_data.data
        pdf_bytes_stream = io.BytesIO(pdf_bytes)
    except FileNotFoundError:
        print(f"오류: 아티팩트 '{file_name}'을 찾을 수 없습니다.")

    try:
        # 업로드된 문서가 PDF인지 확인하는 테스트:
        # PdfReader를 초기화하려고 시도합니다. PDF 구조를 분석하려고 합니다.
        # 손상되었거나 악성인 파일에는 실패하는 강력한 검사입니다.
        reader = PdfReader(pdf_bytes_stream)

        # 간단한 정상성 검사입니다. 파일에 페이지가 없으면 유효한 PDF가 아닙니다.
        if not reader.pages:
            raise PdfReaderError("PDF에 페이지가 없습니다.")
    except Exception as e:
        # 원래 예외를 더 자세한 오류로 감싸세요.
        raise PdfReaderError(f"PDF를 안전하게 구문 분석하지 못했습니다: {e}")

    try:   
        # io.BytesIO를 사용하여 바이트를 파일과 유사한 객체로 처리합니다.
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            full_text = ""
            for page in pdf.pages:
                # 각 페이지에서 텍스트를 추출하여 추가합니다.
                full_text += page.extract_text() + "\n"

        print("PDF에서 텍스트를 성공적으로 추출했습니다.")
        print("\n--- 추출된 텍스트 ---")
        print("전체 텍스트에서 추출된 문자 수: ", len(full_text))
        
        # 추출된 텍스트를 세션 상태에 저장
        tool_context.state["extracted_pdf_text"] = full_text
        tool_context.state["pdf_file_name"] = file_name

    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
    print("------------------------------------------------")

    return "문서가 성공적으로 업로드되었습니다"


def extract_pdf_text(tool_context: ToolContext, pdf_content: str) -> dict:
    """
    PDF 내용에서 텍스트를 추출하여 아티팩트로 저장합니다.
    
    Args:
        tool_context: ADK 도구 컨텍스트
        pdf_content: PDF 파일의 바이트 내용
    
    Returns:
        dict: 텍스트 추출 결과
    """
    try:
        # PDF 바이트 스트림 생성
        pdf_bytes_stream = io.BytesIO(pdf_content.encode() if isinstance(pdf_content, str) else pdf_content)
        
        # PDF 텍스트 추출
        with pdfplumber.open(pdf_bytes_stream) as pdf:
            full_text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
        
        # 추출된 텍스트를 세션 상태에 저장
        tool_context.state["extracted_pdf_text"] = full_text
        
        return {
            "status": "success",
            "message": f"PDF에서 {len(full_text)}자 텍스트 추출 완료",
            "text_length": len(full_text),
            "extracted_text": full_text[:500] + "..." if len(full_text) > 500 else full_text
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"PDF 텍스트 추출 중 오류 발생: {str(e)}"
        }


# FunctionTool로 래핑
pdf_processor_tool = FunctionTool(func=check_uploaded_document)
pdf_text_extractor_tool = FunctionTool(func=extract_pdf_text)
