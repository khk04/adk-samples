"""
유틸리티 테스트
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from doc_question_report_agent.utils import (
    DocumentProcessor, ReportGenerator,
    extract_keywords, calculate_text_similarity, split_text_into_chunks
)


class TestDocumentProcessor:
    """DocumentProcessor 테스트 클래스"""
    
    @pytest.fixture
    def processor(self):
        """테스트용 프로세서 인스턴스 생성"""
        return DocumentProcessor()
    
    def test_processor_initialization(self, processor):
        """프로세서 초기화 테스트"""
        assert processor.supported_extensions is not None
        assert len(processor.supported_extensions) > 0
    
    def test_document_type_detection(self, processor):
        """문서 타입 감지 테스트"""
        assert processor._detect_document_type("test.pdf") == ".pdf"
        assert processor._detect_document_type("test.docx") == ".docx"
        assert processor._detect_document_type("test.txt") == ".txt"
        assert processor._detect_document_type("test.html") == ".html"
        assert processor._detect_document_type("test.md") == ".md"
        assert processor._detect_document_type("test.csv") == ".csv"
        assert processor._detect_document_type("test.xlsx") == ".xlsx"
    
    @pytest.mark.asyncio
    async def test_txt_text_extraction(self, processor):
        """TXT 파일 텍스트 추출 테스트"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("테스트 텍스트 내용입니다.")
            temp_file = f.name
        
        try:
            content = await processor._extract_txt_text(Path(temp_file))
            assert "테스트 텍스트 내용입니다." in content
        finally:
            Path(temp_file).unlink()
    
    @pytest.mark.asyncio
    async def test_html_text_extraction(self, processor):
        """HTML 파일 텍스트 추출 테스트"""
        html_content = """
        <html>
            <head><title>테스트</title></head>
            <body>
                <h1>제목</h1>
                <p>테스트 내용입니다.</p>
                <script>alert('test');</script>
            </body>
        </html>
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html_content)
            temp_file = f.name
        
        try:
            content = await processor._extract_html_text(Path(temp_file))
            assert "제목" in content
            assert "테스트 내용입니다." in content
            assert "alert('test')" not in content  # 스크립트 제거 확인
        finally:
            Path(temp_file).unlink()
    
    @pytest.mark.asyncio
    async def test_md_text_extraction(self, processor):
        """Markdown 파일 텍스트 추출 테스트"""
        md_content = """
        # 제목
        이것은 **굵은** 텍스트입니다.
        - 항목 1
        - 항목 2
        
        `코드` 예시
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(md_content)
            temp_file = f.name
        
        try:
            content = await processor._extract_md_text(Path(temp_file))
            assert "제목" in content
            assert "굵은" in content
            assert "**" not in content  # 마크다운 문법 제거 확인
            assert "`" not in content
        finally:
            Path(temp_file).unlink()
    
    def test_text_cleaning(self, processor):
        """텍스트 정리 테스트"""
        dirty_text = "  여러    공백과\n\n\n줄바꿈이\n있는\n텍스트  "
        cleaned_text = processor._clean_text(dirty_text)
        
        assert "  " not in cleaned_text  # 연속된 공백 제거
        assert "\n\n\n" not in cleaned_text  # 연속된 줄바꿈 제거
        assert cleaned_text.startswith("여러")  # 앞뒤 공백 제거
        assert cleaned_text.endswith("텍스트")


class TestReportGenerator:
    """ReportGenerator 테스트 클래스"""
    
    @pytest.fixture
    def generator(self):
        """테스트용 생성기 인스턴스 생성"""
        return ReportGenerator()
    
    def test_generator_initialization(self, generator):
        """생성기 초기화 테스트"""
        assert generator.templates_dir is not None
        assert generator.output_dir is not None
    
    @pytest.mark.asyncio
    async def test_html_report_generation(self, generator):
        """HTML 리포트 생성 테스트"""
        content = "테스트 내용입니다."
        title = "테스트 리포트"
        
        output_path = await generator.generate_html_report(content, title)
        
        assert Path(output_path).exists()
        assert Path(output_path).suffix == ".html"
        
        # HTML 내용 확인
        with open(output_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            assert title in html_content
            assert content in html_content
            assert "<!DOCTYPE html>" in html_content
        
        # 테스트 파일 정리
        Path(output_path).unlink()
    
    @pytest.mark.asyncio
    async def test_docx_report_generation(self, generator):
        """DOCX 리포트 생성 테스트"""
        content = "테스트 내용입니다."
        title = "테스트 리포트"
        
        output_path = await generator.generate_docx_report(content, title)
        
        assert Path(output_path).exists()
        assert Path(output_path).suffix == ".docx"
        
        # 테스트 파일 정리
        Path(output_path).unlink()
    
    @pytest.mark.asyncio
    async def test_report_format_selection(self, generator):
        """리포트 형식 선택 테스트"""
        content = "테스트 내용"
        title = "테스트"
        
        # HTML 형식
        html_path = await generator.generate_report(content, title, "html")
        assert Path(html_path).suffix == ".html"
        Path(html_path).unlink()
        
        # DOCX 형식
        docx_path = await generator.generate_report(content, title, "docx")
        assert Path(docx_path).suffix == ".docx"
        Path(docx_path).unlink()
        
        # 잘못된 형식
        with pytest.raises(ValueError):
            await generator.generate_report(content, title, "invalid_format")


class TestTextAnalysisUtils:
    """텍스트 분석 유틸리티 테스트 클래스"""
    
    def test_keyword_extraction(self):
        """키워드 추출 테스트"""
        text = "테스트 문서입니다. 테스트는 중요한 과정입니다. 문서 분석을 진행합니다."
        keywords = extract_keywords(text, top_n=5)
        
        assert len(keywords) <= 5
        assert any("테스트" in keyword for keyword, _ in keywords)
        assert all(isinstance(keyword, str) and isinstance(count, int) for keyword, count in keywords)
    
    def test_text_similarity(self):
        """텍스트 유사도 계산 테스트"""
        text1 = "안녕하세요 반갑습니다"
        text2 = "안녕하세요 반갑습니다"
        text3 = "안녕하세요 만나서 반갑습니다"
        
        # 동일한 텍스트
        similarity1 = calculate_text_similarity(text1, text2)
        assert similarity1 == 1.0
        
        # 유사한 텍스트
        similarity2 = calculate_text_similarity(text1, text3)
        assert 0.5 < similarity2 < 1.0
        
        # 완전히 다른 텍스트
        text4 = "완전히 다른 내용입니다"
        similarity3 = calculate_text_similarity(text1, text4)
        assert similarity3 < 0.5
    
    def test_text_chunking(self):
        """텍스트 청킹 테스트"""
        text = "이것은 " + "테스트 " * 100 + "텍스트입니다."
        chunks = split_text_into_chunks(text, chunk_size=50, overlap=10)
        
        assert len(chunks) > 1
        assert all(len(chunk) <= 50 for chunk in chunks)
        
        # 청크 간 겹침 확인
        if len(chunks) > 1:
            first_chunk = chunks[0]
            second_chunk = chunks[1]
            overlap_text = first_chunk[-10:]  # 마지막 10자
            assert overlap_text in second_chunk


# 테스트 설정
pytest_plugins = ['pytest_asyncio']