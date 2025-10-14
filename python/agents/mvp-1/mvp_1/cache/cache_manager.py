"""
통합 캐시 매니저

데이터 캐시와 분석 캐시를 통합 관리하는 매니저 클래스입니다.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path

from .data_cache import DataCache
from .analysis_cache import AnalysisCache

logger = logging.getLogger(__name__)


class CacheManager:
    """통합 캐시 관리자"""
    
    def __init__(self, cache_base_dir: str = "data/cache"):
        """
        캐시 매니저 초기화
        
        Args:
            cache_base_dir: 캐시 기본 디렉토리
        """
        self.cache_base_dir = Path(cache_base_dir)
        self.cache_base_dir.mkdir(parents=True, exist_ok=True)
        
        # 개별 캐시 인스턴스 초기화
        self.data_cache = DataCache(str(self.cache_base_dir / "data"))
        self.analysis_cache = AnalysisCache(str(self.cache_base_dir / "analysis"))
        
        # 캐시 정리 설정
        self.auto_cleanup_enabled = True
        self.cleanup_interval = timedelta(hours=6)  # 6시간마다 정리
        self.last_cleanup = datetime.now()
        
        logger.info(f"CacheManager 초기화 완료: {self.cache_base_dir}")
    
    def get_data(self, file_path: str):
        """데이터 캐시에서 데이터 조회"""
        return self.data_cache.get_cached_data(file_path)
    
    def cache_data(self, file_path: str, data):
        """데이터 캐시에 데이터 저장"""
        self.data_cache.cache_data(file_path, data)
    
    def get_analysis(self, file_path: str, analysis_type: str, params: Dict[str, Any]):
        """분석 캐시에서 분석 결과 조회"""
        return self.analysis_cache.get_cached_analysis(file_path, analysis_type, params)
    
    def cache_analysis(self, file_path: str, analysis_type: str, params: Dict[str, Any], result: Dict[str, Any]):
        """분석 캐시에 분석 결과 저장"""
        self.analysis_cache.cache_analysis(file_path, analysis_type, params, result)
    
    def clear_all_cache(self):
        """모든 캐시 정리"""
        logger.info("전체 캐시 정리 시작")
        self.data_cache.clear_cache()
        self.analysis_cache.clear_cache()
        logger.info("전체 캐시 정리 완료")
    
    def clear_file_cache(self, file_path: str):
        """특정 파일의 모든 캐시 정리"""
        logger.info(f"파일 캐시 정리 시작: {file_path}")
        self.data_cache.clear_cache(file_path)
        self.analysis_cache.clear_cache(file_path=file_path)
        logger.info(f"파일 캐시 정리 완료: {file_path}")
    
    def clear_analysis_cache(self, analysis_type: str):
        """특정 분석 유형의 캐시 정리"""
        logger.info(f"분석 캐시 정리 시작: {analysis_type}")
        self.analysis_cache.clear_cache(analysis_type=analysis_type)
        logger.info(f"분석 캐시 정리 완료: {analysis_type}")
    
    def auto_cleanup(self):
        """자동 캐시 정리 (만료된 캐시 제거)"""
        if not self.auto_cleanup_enabled:
            return
        
        now = datetime.now()
        if now - self.last_cleanup < self.cleanup_interval:
            return
        
        logger.info("자동 캐시 정리 시작")
        
        try:
            # 만료된 데이터 캐시 정리
            self._cleanup_expired_data_cache()
            
            # 만료된 분석 캐시 정리
            self._cleanup_expired_analysis_cache()
            
            self.last_cleanup = now
            logger.info("자동 캐시 정리 완료")
            
        except Exception as e:
            logger.error(f"자동 캐시 정리 실패: {e}")
    
    def _cleanup_expired_data_cache(self):
        """만료된 데이터 캐시 정리"""
        try:
            cache_dir = Path(self.data_cache.cache_dir)
            current_time = datetime.now()
            ttl = self.data_cache.cache_ttl
            
            removed_count = 0
            for cache_file in cache_dir.glob("*.pkl"):
                try:
                    with open(cache_file, 'rb') as f:
                        import pickle
                        cache_entry = pickle.load(f)
                        cache_time = cache_entry['timestamp']
                        
                        if current_time - cache_time > ttl:
                            cache_file.unlink()
                            removed_count += 1
                            
                except Exception as e:
                    logger.warning(f"데이터 캐시 파일 정리 실패: {cache_file}, 오류: {e}")
            
            if removed_count > 0:
                logger.info(f"만료된 데이터 캐시 {removed_count}개 정리 완료")
                
        except Exception as e:
            logger.error(f"데이터 캐시 정리 실패: {e}")
    
    def _cleanup_expired_analysis_cache(self):
        """만료된 분석 캐시 정리"""
        try:
            cache_dir = Path(self.analysis_cache.cache_dir)
            current_time = datetime.now()
            ttl = self.analysis_cache.cache_ttl
            
            removed_count = 0
            for cache_file in cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        import json
                        cache_entry = json.load(f)
                        cache_time = datetime.fromisoformat(cache_entry['timestamp'])
                        
                        if current_time - cache_time > ttl:
                            cache_file.unlink()
                            removed_count += 1
                            
                except Exception as e:
                    logger.warning(f"분석 캐시 파일 정리 실패: {cache_file}, 오류: {e}")
            
            if removed_count > 0:
                logger.info(f"만료된 분석 캐시 {removed_count}개 정리 완료")
                
        except Exception as e:
            logger.error(f"분석 캐시 정리 실패: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """전체 캐시 통계 정보 반환"""
        try:
            data_stats = self.data_cache.get_cache_stats()
            analysis_stats = self.analysis_cache.get_cache_stats()
            
            # 전체 통계 계산
            total_cache_size = data_stats.get('disk_cache_size_mb', 0) + analysis_stats.get('disk_cache_size_mb', 0)
            total_cache_count = data_stats.get('disk_cache_count', 0) + analysis_stats.get('disk_cache_count', 0)
            
            return {
                'total_cache_size_mb': round(total_cache_size, 2),
                'total_cache_count': total_cache_count,
                'data_cache': data_stats,
                'analysis_cache': analysis_stats,
                'auto_cleanup_enabled': self.auto_cleanup_enabled,
                'last_cleanup': self.last_cleanup.isoformat(),
                'next_cleanup': (self.last_cleanup + self.cleanup_interval).isoformat()
            }
            
        except Exception as e:
            logger.error(f"캐시 통계 조회 실패: {e}")
            return {}
    
    def optimize_cache(self):
        """캐시 최적화 (크기 제한, 압축 등)"""
        logger.info("캐시 최적화 시작")
        
        try:
            # 자동 정리 실행
            self.auto_cleanup()
            
            # 메모리 캐시 크기 최적화
            self._optimize_memory_cache()
            
            logger.info("캐시 최적화 완료")
            
        except Exception as e:
            logger.error(f"캐시 최적화 실패: {e}")
    
    def _optimize_memory_cache(self):
        """메모리 캐시 최적화"""
        try:
            # 데이터 캐시 메모리 최적화
            if len(self.data_cache.memory_cache) > self.data_cache.max_memory_cache_size:
                # 가장 오래된 항목들 제거
                sorted_items = sorted(
                    self.data_cache.memory_cache.items(),
                    key=lambda x: x[1]['timestamp']
                )
                
                items_to_remove = len(sorted_items) - self.data_cache.max_memory_cache_size
                for key, _ in sorted_items[:items_to_remove]:
                    del self.data_cache.memory_cache[key]
                
                logger.info(f"데이터 캐시 메모리 최적화: {items_to_remove}개 항목 제거")
            
            # 분석 캐시 메모리 최적화
            if len(self.analysis_cache.memory_cache) > self.analysis_cache.max_memory_cache_size:
                # 가장 오래된 항목들 제거
                sorted_items = sorted(
                    self.analysis_cache.memory_cache.items(),
                    key=lambda x: x[1]['timestamp']
                )
                
                items_to_remove = len(sorted_items) - self.analysis_cache.max_memory_cache_size
                for key, _ in sorted_items[:items_to_remove]:
                    del self.analysis_cache.memory_cache[key]
                
                logger.info(f"분석 캐시 메모리 최적화: {items_to_remove}개 항목 제거")
                
        except Exception as e:
            logger.error(f"메모리 캐시 최적화 실패: {e}")


# 전역 캐시 매니저 인스턴스
cache_manager = CacheManager()