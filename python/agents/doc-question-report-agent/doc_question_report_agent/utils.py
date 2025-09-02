"""
유틸리티 클래스들
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import PyPDF2
from docx import Document
import pandas as pd
from bs4 import BeautifulSoup
from loguru import logger


class DocumentProcessor:
    """문서 처리 유틸리티 클래스"""
    
    def __init__(self):
        self.supported_extensions = {
            '.pdf': self._extract_pdf_text,
            '.docx': self._extract_docx_text,
            '.txt': self._extract_txt_text,
            '.html': self._extract_html_text,
            '.htm': self._extract_html_text,
            '.md': self._extract_md_text,
            '.csv': self._extract_csv_text,
            '.xlsx': self._extract_excel_text,
            '.xls': self._extract_excel_text
        }
    
    async def extract_text(self, file_path: str, document_type: str) -> str:
        """문서에서 텍스트를 추출합니다."""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
            
            extension = file_path.suffix.lower()
            
            if extension not in self.supported_extensions:
                raise ValueError(f"지원하지 않는 파일 형식: {extension}")
            
            # 파일 크기 확인
            file_size = file_path.stat().st_size
            if file_size > 100 * 1024 * 1024:  # 100MB 제한
                raise ValueError(f"파일이 너무 큽니다: {file_size / (1024*1024):.2f}MB")
            
            # 텍스트 추출
            extractor = self.supported_extensions[extension]
            text = await extractor(file_path)
            
            # 텍스트 정리
            cleaned_text = self._clean_text(text)
            
            logger.info(f"텍스트 추출 완료: {file_path.name}, 길이: {len(cleaned_text)}")
            return cleaned_text
            
        except Exception as e:
            logger.error(f"텍스트 추출 실패: {file_path}, 오류: {str(e)}")
            raise
    
    async def _extract_pdf_text(self, file_path: Path) -> str:
        """PDF에서 텍스트를 추출합니다."""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
                
                return text
                
        except Exception as e:
            logger.error(f"PDF 텍스트 추출 실패: {file_path}, 오류: {str(e)}")
            raise
    
    async def _extract_docx_text(self, file_path: Path) -> str:
        """DOCX에서 텍스트를 추출합니다."""
        try:
            doc = Document(file_path)
            text = ""
            
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            # 테이블에서도 텍스트 추출
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        text += cell.text + "\t"
                    text += "\n"
            
            return text
            
        except Exception as e:
            logger.error(f"DOCX 텍스트 추출 실패: {file_path}, 오류: {str(e)}")
            raise
    
    async def _extract_txt_text(self, file_path: Path) -> str:
        """TXT 파일에서 텍스트를 추출합니다."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
                
        except UnicodeDecodeError:
            # UTF-8 실패 시 다른 인코딩 시도
            try:
                with open(file_path, 'r', encoding='cp949') as file:
                    return file.read()
            except Exception as e:
                logger.error(f"TXT 텍스트 추출 실패: {file_path}, 오류: {str(e)}")
                raise
    
    async def _extract_html_text(self, file_path: Path) -> str:
        """HTML에서 텍스트를 추출합니다."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file.read(), 'html.parser')
                
                # 스크립트와 스타일 태그 제거
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # 텍스트 추출
                text = soup.get_text()
                
                # 줄바꿈 정리
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                
                return text
                
        except Exception as e:
            logger.error(f"HTML 텍스트 추출 실패: {file_path}, 오류: {str(e)}")
            raise
    
    async def _extract_md_text(self, file_path: Path) -> str:
        """Markdown에서 텍스트를 추출합니다."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
                # Markdown 문법 제거
                # 헤더 제거
                content = re.sub(r'^#+\s+', '', content, flags=re.MULTILINE)
                # 굵게/기울임 제거
                content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
                content = re.sub(r'\*(.*?)\*', r'\1', content)
                # 코드 블록 제거
                content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
                # 인라인 코드 제거
                content = re.sub(r'`(.*?)`', r'\1', content)
                # 링크 제거
                content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
                
                return content
                
        except Exception as e:
            logger.error(f"Markdown 텍스트 추출 실패: {file_path}, 오류: {str(e)}")
            raise
    
    async def _extract_csv_text(self, file_path: Path) -> str:
        """CSV에서 텍스트를 추출합니다."""
        try:
            df = pd.read_csv(file_path)
            
            # 데이터프레임을 텍스트로 변환
            text = df.to_string(index=False)
            
            # 컬럼명 추가
            text = f"컬럼: {', '.join(df.columns)}\n\n{text}"
            
            return text
            
        except Exception as e:
            logger.error(f"CSV 텍스트 추출 실패: {file_path}, 오류: {str(e)}")
            raise
    
    async def _extract_excel_text(self, file_path: Path) -> str:
        """Excel에서 텍스트를 추출합니다."""
        try:
            # 모든 시트 읽기
            excel_file = pd.ExcelFile(file_path)
            text = ""
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                text += f"\n=== 시트: {sheet_name} ===\n"
                text += df.to_string(index=False) + "\n"
            
            return text
            
        except Exception as e:
            logger.error(f"Excel 텍스트 추출 실패: {file_path}, 오류: {str(e)}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """추출된 텍스트를 정리합니다."""
        if not text:
            return ""
        
        # 연속된 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        # 연속된 줄바꿈 제거
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # 앞뒤 공백 제거
        text = text.strip()
        
        return text


class ReportGenerator:
    """리포트 생성 유틸리티 클래스"""
    
    def __init__(self):
        self.templates_dir = Path(__file__).parent / "templates"
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
    
    async def generate_pdf_report(self, content: str, title: str, output_path: Optional[str] = None) -> str:
        """PDF 리포트를 생성합니다."""
        try:
            if output_path is None:
                output_path = self.output_dir / f"{title.replace(' ', '_')}.pdf"
            
            # ReportLab을 사용한 PDF 생성
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            
            doc = SimpleDocTemplate(str(output_path), pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # 제목
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                alignment=1  # 중앙 정렬
            )
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 12))
            
            # 내용
            content_style = ParagraphStyle(
                'CustomContent',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=12,
                leading=14
            )
            
            # 내용을 단락으로 분할
            paragraphs = content.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    story.append(Paragraph(para.strip(), content_style))
                    story.append(Spacer(1, 6))
            
            doc.build(story)
            
            logger.info(f"PDF 리포트 생성 완료: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"PDF 리포트 생성 실패: {str(e)}")
            raise
    
    async def generate_html_report(self, content: str, title: str, output_path: Optional[str] = None) -> str:
        """HTML 리포트를 생성합니다."""
        try:
            if output_path is None:
                output_path = self.output_dir / f"{title.replace(' ', '_')}.html"
            
            html_template = f"""
            <!DOCTYPE html>
            <html lang="ko">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{title}</title>
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        line-height: 1.6;
                        margin: 0;
                        padding: 20px;
                        background-color: #f5f5f5;
                    }}
                    .container {{
                        max-width: 800px;
                        margin: 0 auto;
                        background-color: white;
                        padding: 30px;
                        border-radius: 8px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    h1 {{
                        color: #2c3e50;
                        text-align: center;
                        border-bottom: 3px solid #3498db;
                        padding-bottom: 10px;
                    }}
                    .content {{
                        margin-top: 20px;
                    }}
                    p {{
                        margin-bottom: 15px;
                        text-align: justify;
                    }}
                    .timestamp {{
                        text-align: center;
                        color: #7f8c8d;
                        font-style: italic;
                        margin-top: 30px;
                        border-top: 1px solid #ecf0f1;
                        padding-top: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>{title}</h1>
                    <div class="content">
                        {content.replace(chr(10), '<br>')}
                    </div>
                    <div class="timestamp">
                        생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </div>
                </div>
            </body>
            </html>
            """
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_template)
            
            logger.info(f"HTML 리포트 생성 완료: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"HTML 리포트 생성 실패: {str(e)}")
            raise
    
    async def generate_docx_report(self, content: str, title: str, output_path: Optional[str] = None) -> str:
        """DOCX 리포트를 생성합니다."""
        try:
            if output_path is None:
                output_path = self.output_dir / f"{title.replace(' ', '_')}.docx"
            
            doc = Document()
            
            # 제목
            title_para = doc.add_heading(title, 0)
            title_para.alignment = 1  # 중앙 정렬
            
            # 내용
            content_para = doc.add_paragraph()
            content_para.add_run(content)
            
            # 저장
            doc.save(str(output_path))
            
            logger.info(f"DOCX 리포트 생성 완료: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"DOCX 리포트 생성 실패: {str(e)}")
            raise
    
    async def generate_report(self, content: str, title: str, format_type: str, 
                            output_path: Optional[str] = None) -> str:
        """지정된 형식으로 리포트를 생성합니다."""
        try:
            format_type = format_type.lower()
            
            if format_type == 'pdf':
                return await self.generate_pdf_report(content, title, output_path)
            elif format_type == 'html':
                return await self.generate_html_report(content, title, output_path)
            elif format_type == 'docx':
                return await self.generate_docx_report(content, title, output_path)
            else:
                raise ValueError(f"지원하지 않는 형식: {format_type}")
                
        except Exception as e:
            logger.error(f"리포트 생성 실패: {str(e)}")
            raise


# 텍스트 분석 유틸리티 함수들
def extract_keywords(text: str, top_n: int = 10) -> List[Tuple[str, int]]:
    """텍스트에서 키워드를 추출합니다."""
    from collections import Counter
    import re
    
    # 한글, 영문, 숫자만 포함하는 단어 추출
    words = re.findall(r'[가-힣a-zA-Z0-9]+', text.lower())
    
    # 불용어 제거 (간단한 버전)
    stopwords = {'이', '그', '저', '것', '수', '등', '때', '곳', '말', '일', '년', '월', '일'}
    words = [word for word in words if word not in stopwords and len(word) > 1]
    
    # 빈도수 계산
    word_counts = Counter(words)
    
    return word_counts.most_common(top_n)


def calculate_text_similarity(text1: str, text2: str) -> float:
    """두 텍스트 간의 유사도를 계산합니다."""
    from difflib import SequenceMatcher
    
    return SequenceMatcher(None, text1, text2).ratio()


def split_text_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """텍스트를 청크로 분할합니다."""
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        
        if end >= len(text):
            break
            
        start = end - overlap
    
    return chunks