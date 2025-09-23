"""
이미지 생성 및 관리 유틸리티

차트 이미지 생성, 저장, 복사 등의 공통 기능을 제공합니다.
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import matplotlib.pyplot as plt

from ....config import REPORTS_DIR


class ImageConfig:
    """이미지 생성 설정"""
    DEFAULT_DPI = 300
    DEFAULT_FIGSIZE = (10, 6)
    CHART_SAVE_DIR = REPORTS_DIR / "charts"
    MAX_CHARTS = 5


def save_chart_image(
    plt_figure: plt.Figure, 
    timestamp: str, 
    index: int, 
    chart_type: str = "chart",
    dpi: int = None,
    target_dir: Path = None
) -> str:
    """
    공통 차트 이미지 저장 함수
    
    Args:
        plt_figure: matplotlib Figure 객체
        timestamp: 타임스탬프 문자열
        index: 차트 인덱스
        chart_type: 차트 유형
        dpi: 이미지 DPI (기본값: ImageConfig.DEFAULT_DPI)
        target_dir: 저장할 디렉토리 (기본값: ImageConfig.CHART_SAVE_DIR)
    
    Returns:
        str: 저장된 이미지 파일 경로
    """
    if dpi is None:
        dpi = ImageConfig.DEFAULT_DPI
    
    if target_dir is None:
        target_dir = ImageConfig.CHART_SAVE_DIR
    
    # 디렉토리 생성
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # 파일명 생성
    filename = f"{chart_type}_{timestamp}_{index}.png"
    image_path = str(target_dir / filename)
    
    try:
        # 이미지 저장
        plt_figure.savefig(
            image_path, 
            dpi=dpi, 
            bbox_inches='tight', 
            facecolor='white',
            format='png'
        )
        print(f"차트 이미지 저장 완료: {image_path}")
        return image_path
        
    except Exception as e:
        print(f"차트 이미지 저장 실패: {e}")
        return None
    # Figure 객체 정리는 호출하는 쪽에서 처리


def copy_chart_images(
    chart_image_files: List[str], 
    target_dir: Path, 
    use_standard_names: bool = True,
    max_files: int = None
) -> List[str]:
    """
    통합된 차트 이미지 복사 함수
    
    Args:
        chart_image_files: 복사할 이미지 파일 경로 리스트
        target_dir: 대상 디렉토리
        use_standard_names: 표준화된 파일명 사용 여부 (chart_0.png, chart_1.png, ...)
        max_files: 최대 복사할 파일 수 (기본값: ImageConfig.MAX_CHARTS)
    
    Returns:
        List[str]: 복사된 파일 경로 리스트
    """
    if max_files is None:
        max_files = ImageConfig.MAX_CHARTS
    
    if not chart_image_files:
        print("복사할 차트 이미지 파일이 없습니다.")
        return []
    
    # 대상 디렉토리 생성
    target_dir.mkdir(parents=True, exist_ok=True)
    
    copied_files = []
    
    try:
        print(f"차트 이미지 복사 시작: {len(chart_image_files)}개 파일")
        
        for i, image_file in enumerate(chart_image_files[:max_files]):
            if not os.path.exists(image_file):
                print(f"차트 이미지 파일이 존재하지 않음: {image_file}")
                continue
            
            if use_standard_names:
                # 표준화된 파일명 사용 (chart_0.png, chart_1.png, ...)
                filename = f"chart_{i}.png"
            else:
                # 원본 파일명 사용
                filename = os.path.basename(image_file)
            
            destination = target_dir / filename
            
            # 파일이 이미 존재하지 않는 경우에만 복사
            if not destination.exists():
                shutil.copy2(image_file, destination)
                copied_files.append(str(destination))
                print(f"차트 이미지 복사 완료: {image_file} -> {destination}")
            else:
                print(f"차트 이미지 이미 존재: {destination}")
                copied_files.append(str(destination))
        
        print(f"차트 이미지 복사 완료: {len(copied_files)}개 파일 처리")
        return copied_files
        
    except Exception as e:
        print(f"차트 이미지 복사 중 오류: {e}")
        return copied_files


def get_chart_image_path(
    index: int, 
    charts_dir: Path = None, 
    use_standard_names: bool = True
) -> str:
    """
    차트 이미지 경로를 생성합니다.
    
    Args:
        index: 차트 인덱스
        charts_dir: 차트 디렉토리 (기본값: None)
        use_standard_names: 표준화된 파일명 사용 여부
    
    Returns:
        str: 차트 이미지 경로
    """
    if use_standard_names:
        filename = f"chart_{index}.png"
    else:
        filename = f"chart_{index}.png"  # 기본값
    
    if charts_dir:
        return f"./charts/{filename}"
    else:
        return filename


def cleanup_old_charts(days_to_keep: int = 7) -> int:
    """
    오래된 차트 이미지 파일들을 정리합니다.
    
    Args:
        days_to_keep: 보관할 일수
    
    Returns:
        int: 삭제된 파일 수
    """
    if not ImageConfig.CHART_SAVE_DIR.exists():
        return 0
    
    deleted_count = 0
    cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
    
    try:
        for file_path in ImageConfig.CHART_SAVE_DIR.glob("*.png"):
            if file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
                deleted_count += 1
                print(f"오래된 차트 파일 삭제: {file_path}")
        
        print(f"총 {deleted_count}개의 오래된 차트 파일을 삭제했습니다.")
        return deleted_count
        
    except Exception as e:
        print(f"차트 파일 정리 중 오류: {e}")
        return deleted_count


def get_chart_image_info(image_path: str) -> dict:
    """
    차트 이미지 파일 정보를 반환합니다.
    
    Args:
        image_path: 이미지 파일 경로
    
    Returns:
        dict: 이미지 파일 정보
    """
    if not os.path.exists(image_path):
        return {"exists": False}
    
    stat = os.stat(image_path)
    return {
        "exists": True,
        "size": stat.st_size,
        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "filename": os.path.basename(image_path)
    }