"""
유틸리티 클래스들
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import PyPDF2
from docx import Document

# 선택적 import
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False
    BeautifulSoup = None

from loguru import logger


class DocumentProcessor:
    """문서 처리 유틸리티 클래스"""
    
    def __init__(self):
        self.supported_extensions = {
            '.txt': self._process_txt,
            '.pdf': self._process_pdf,
            '.docx': self._process_docx,
            '.xlsx': self._process_xlsx,
            '.csv': self._process_csv,
            '.html': self._process_html
        }
        logger.info("DocumentProcessor 초기화 완료")
    
    def process_document(self, file_path: str) -> str:
        """문서를 처리하여 텍스트를 추출"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
            
            extension = file_path.suffix.lower()
            if extension not in self.supported_extensions:
                raise ValueError(f"지원하지 않는 파일 형식입니다: {extension}")
            
            logger.info(f"문서 처리 시작: {file_path}")
            text = self.supported_extensions[extension](file_path)
            logger.info(f"문서 처리 완료: {file_path}")
            
            return text
            
        except Exception as e:
            logger.error(f"문서 처리 실패: {str(e)}")
            raise
    
    def _process_txt(self, file_path: Path) -> str:
        """텍스트 파일 처리"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _process_pdf(self, file_path: Path) -> str:
        """PDF 파일 처리"""
        if not PyPDF2:
            raise ImportError("PyPDF2가 설치되지 않았습니다")
        
        text = ""
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    def _process_docx(self, file_path: Path) -> str:
        """Word 문서 처리"""
        if not Document:
            raise ImportError("python-docx가 설치되지 않았습니다")
        
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    
    def _process_xlsx(self, file_path: Path) -> str:
        """Excel 파일 처리"""
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas가 설치되지 않았습니다")
        
        df = pd.read_excel(file_path)
        return df.to_string()
    
    def _process_csv(self, file_path: Path) -> str:
        """CSV 파일 처리"""
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas가 설치되지 않았습니다")
        
        df = pd.read_csv(file_path)
        return df.to_string()
    
    def _process_html(self, file_path: Path) -> str:
        """HTML 파일 처리"""
        if not BEAUTIFULSOUP_AVAILABLE:
            raise ImportError("beautifulsoup4가 설치되지 않았습니다")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            return soup.get_text()


