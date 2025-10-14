"""
데이터 캐시 시스템

파일 읽기 작업을 캐싱하여 API 키 낭비를 방지하고 성능을 향상시킵니다.
"""

import pandas as pd
import hashlib
import pickle
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class DataCache:
    """데이터 파일 캐싱을 위한 클래스"""
    
    def __init__(self, cache_dir: str = "data/cache/data"):
        """
        데이터 캐시 초기화
        
        Args:
            cache_dir: 캐시 디렉토리 경로
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.memory_cache = {}  # 메모리 캐시
        self.cache_ttl = timedelta(hours=24)  # 24시간 TTL
        self.max_memory_cache_size = 100  # 메모리 캐시 최대 크기
        
        logger.info(f"DataCache 초기화 완료: {self.cache_dir}")
    
    def get_file_hash(self, file_path: str) -> str:
        """
        파일의 해시값을 계산하여 캐시 키로 사용
        
        Args:
            file_path: 파일 경로
            
        Returns:
            파일의 MD5 해시값
        """
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"파일 해시 계산 실패: {file_path}, 오류: {e}")
            # 파일 경로를 기반으로 대체 해시 생성
            return hashlib.md5(file_path.encode()).hexdigest()
    
    def get_cached_data(self, file_path: str) -> Optional[pd.DataFrame]:
        """
        캐시된 데이터를 반환
        
        Args:
            file_path: 파일 경로
            
        Returns:
            캐시된 DataFrame 또는 None
        """
        try:
            file_hash = self.get_file_hash(file_path)
            
            # 메모리 캐시 확인
            if file_hash in self.memory_cache:
                cache_entry = self.memory_cache[file_hash]
                if datetime.now() - cache_entry['timestamp'] < self.cache_ttl:
                    logger.info(f"메모리 캐시에서 데이터 로드: {file_path}")
                    return cache_entry['data']
                else:
                    # 만료된 캐시 제거
                    del self.memory_cache[file_hash]
            
            # 디스크 캐시 확인
            cache_file = self.cache_dir / f"{file_hash}.pkl"
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    cache_entry = pickle.load(f)
                    if datetime.now() - cache_entry['timestamp'] < self.cache_ttl:
                        # 메모리 캐시에 로드
                        self._add_to_memory_cache(file_hash, cache_entry)
                        logger.info(f"디스크 캐시에서 데이터 로드: {file_path}")
                        return cache_entry['data']
                    else:
                        # 만료된 캐시 파일 삭제
                        cache_file.unlink()
            
            return None
            
        except Exception as e:
            logger.error(f"캐시된 데이터 조회 실패: {file_path}, 오류: {e}")
            return None
    
    def cache_data(self, file_path: str, data: pd.DataFrame):
        """
        데이터를 캐시에 저장
        
        Args:
            file_path: 파일 경로
            data: 저장할 DataFrame
        """
        try:
            file_hash = self.get_file_hash(file_path)
            cache_entry = {
                'data': data,
                'timestamp': datetime.now(),
                'file_path': file_path,
                'file_size': len(data),
                'columns': list(data.columns)
            }
            
            # 메모리 캐시에 저장
            self._add_to_memory_cache(file_hash, cache_entry)
            
            # 디스크 캐시에 저장
            cache_file = self.cache_dir / f"{file_hash}.pkl"
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_entry, f)
            
            logger.info(f"데이터 캐시 저장 완료: {file_path} ({len(data)}행, {len(data.columns)}열)")
            
        except Exception as e:
            logger.error(f"데이터 캐시 저장 실패: {file_path}, 오류: {e}")
    
    def _add_to_memory_cache(self, file_hash: str, cache_entry: Dict[str, Any]):
        """메모리 캐시에 항목 추가 (크기 제한 적용)"""
        # 메모리 캐시 크기 제한
        if len(self.memory_cache) >= self.max_memory_cache_size:
            # 가장 오래된 항목 제거
            oldest_key = min(self.memory_cache.keys(), 
                           key=lambda k: self.memory_cache[k]['timestamp'])
            del self.memory_cache[oldest_key]
        
        self.memory_cache[file_hash] = cache_entry
    
    def clear_cache(self, file_path: Optional[str] = None):
        """
        캐시 정리
        
        Args:
            file_path: 특정 파일의 캐시만 정리 (None이면 전체 정리)
        """
        try:
            if file_path:
                file_hash = self.get_file_hash(file_path)
                
                # 메모리 캐시에서 제거
                if file_hash in self.memory_cache:
                    del self.memory_cache[file_hash]
                
                # 디스크 캐시에서 제거
                cache_file = self.cache_dir / f"{file_hash}.pkl"
                if cache_file.exists():
                    cache_file.unlink()
                
                logger.info(f"특정 파일 캐시 정리 완료: {file_path}")
            else:
                # 전체 캐시 정리
                self.memory_cache.clear()
                
                # 디스크 캐시 파일들 삭제
                for cache_file in self.cache_dir.glob("*.pkl"):
                    cache_file.unlink()
                
                logger.info("전체 캐시 정리 완료")
                
        except Exception as e:
            logger.error(f"캐시 정리 실패: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 정보 반환"""
        try:
            memory_count = len(self.memory_cache)
            disk_count = len(list(self.cache_dir.glob("*.pkl")))
            
            # 디스크 캐시 크기 계산
            disk_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.pkl"))
            
            return {
                'memory_cache_count': memory_count,
                'disk_cache_count': disk_count,
                'disk_cache_size_mb': round(disk_size / (1024 * 1024), 2),
                'cache_dir': str(self.cache_dir),
                'ttl_hours': self.cache_ttl.total_seconds() / 3600
            }
        except Exception as e:
            logger.error(f"캐시 통계 조회 실패: {e}")
            return {}


# 전역 데이터 캐시 인스턴스
data_cache = DataCache()