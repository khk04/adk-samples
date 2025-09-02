"""
배포 스크립트
"""

import os
import sys
import subprocess
from pathlib import Path
from loguru import logger


def install_dependencies():
    """의존성을 설치합니다."""
    try:
        logger.info("의존성 설치 시작...")
        
        # pip 업그레이드
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        
        # 프로젝트 의존성 설치
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], 
                      check=True, capture_output=True)
        
        logger.info("의존성 설치 완료")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"의존성 설치 실패: {e}")
        return False


def create_directories():
    """필요한 디렉토리를 생성합니다."""
    try:
        logger.info("디렉토리 생성 시작...")
        
        directories = [
            "output",
            "uploads",
            "temp",
            "logs"
        ]
        
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
            logger.info(f"디렉토리 생성: {directory}")
        
        logger.info("디렉토리 생성 완료")
        return True
        
    except Exception as e:
        logger.error(f"디렉토리 생성 실패: {e}")
        return False


def setup_environment():
    """환경 설정을 초기화합니다."""
    try:
        logger.info("환경 설정 시작...")
        
        # .env 파일이 없으면 예시 파일 복사
        env_file = Path(".env")
        env_example = Path("../env.example")
        
        if not env_file.exists() and env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            logger.info(".env 파일 생성됨")
        
        # 환경 변수 로드
        if env_file.exists():
            from dotenv import load_dotenv
            load_dotenv()
            logger.info("환경 변수 로드됨")
        
        logger.info("환경 설정 완료")
        return True
        
    except Exception as e:
        logger.error(f"환경 설정 실패: {e}")
        return False


def run_tests():
    """테스트를 실행합니다."""
    try:
        logger.info("테스트 실행 시작...")
        
        result = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("테스트 통과")
            return True
        else:
            logger.warning(f"테스트 실패: {result.stdout}")
            return False
            
    except Exception as e:
        logger.error(f"테스트 실행 실패: {e}")
        return False


def main():
    """메인 배포 함수"""
    logger.info("DocQuestionReportAgent 배포 시작")
    
    # 1. 의존성 설치
    if not install_dependencies():
        logger.error("의존성 설치 실패로 배포 중단")
        return False
    
    # 2. 디렉토리 생성
    if not create_directories():
        logger.error("디렉토리 생성 실패로 배포 중단")
        return False
    
    # 3. 환경 설정
    if not setup_environment():
        logger.error("환경 설정 실패로 배포 중단")
        return False
    
    # 4. 테스트 실행
    if not run_tests():
        logger.warning("테스트 실패했지만 배포 계속 진행")
    
    logger.info("DocQuestionReportAgent 배포 완료")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)