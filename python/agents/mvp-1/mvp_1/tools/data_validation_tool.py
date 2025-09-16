"""데이터 검증 도구"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from google.adk.tools.function_tool import FunctionTool
import pandas as pd
import json
import os
import glob
from ..config import VDATA_DIR, DEFAULT_REQUIRED_COLUMNS, DEFAULT_MIN_ROWS


class DataValidationInput(BaseModel):
    """데이터 검증 입력"""
    data_directory: str = Field(..., description="검증할 데이터 디렉토리 경로 (예: /path/to/data 또는 data/generated_sales_data)")
    required_columns: List[str] = Field(default=[], description="필수 컬럼 목록 (예: ['월', '지역', '상품군', '매출액'])")
    min_rows: int = Field(default=1, description="최소 행 수 (기본값: 1)")


class DataValidationOutput(BaseModel):
    """데이터 검증 출력"""
    success: bool = Field(..., description="검증 성공 여부")
    is_data_ready: bool = Field(..., description="데이터 준비 완료 여부")
    validation_summary: Dict[str, Any] = Field(default_factory=dict, description="검증 요약 정보")
    file_analysis: List[Dict[str, Any]] = Field(default_factory=list, description="파일별 분석 결과")
    issues: List[str] = Field(default_factory=list, description="발견된 문제점")
    recommendations: List[str] = Field(default_factory=list, description="개선 권장사항")
    error_message: str = Field(default="", description="오류 메시지")


@FunctionTool
def validate_data(data_directory: Optional[str] = None, required_columns: Optional[List[str]] = None, min_rows: Optional[int] = None) -> DataValidationOutput:
    """
    사용자 데이터가 분석에 준비되어 있는지 검증합니다.
    
    이 도구는 사용자가 "데이터 확인해줘", "내 데이터가 준비되어 있어?" 등의 요청을 할 때 사용됩니다.
    데이터 파일의 존재, 형식, 구조, 품질을 종합적으로 확인하고 사용자에게 친근하게 결과를 제공합니다.
    
    사용 예시:
    - 데이터 확인 요청: "내 데이터 상태를 확인해줘"
    - 리포트 생성 전 검증: "리포트를 만들어줘" (자동으로 데이터 검증 후 진행)
    """
    try:
        # 매개변수 기본값 설정 (config 사용)
        if data_directory is None:
            data_directory = str(VDATA_DIR)
        if required_columns is None:
            required_columns = DEFAULT_REQUIRED_COLUMNS
        if min_rows is None:
            min_rows = DEFAULT_MIN_ROWS
        
        # 디렉토리 존재 확인
        if not os.path.exists(data_directory):
            return DataValidationOutput(
                success=False,
                is_data_ready=False,
                error_message=f"데이터 디렉토리를 찾을 수 없습니다: {data_directory}"
            )
        
        # 지원되는 파일 형식 찾기
        csv_files = glob.glob(os.path.join(data_directory, "*.csv"))
        excel_files = glob.glob(os.path.join(data_directory, "*.xlsx")) + glob.glob(os.path.join(data_directory, "*.xls"))
        all_files = csv_files + excel_files
        
        if not all_files:
            return DataValidationOutput(
                success=True,
                is_data_ready=False,
                issues=["데이터 파일이 없습니다"],
                recommendations=["CSV 또는 Excel 파일을 데이터 디렉토리에 추가해주세요"],
                validation_summary={
                    "total_files": 0,
                    "supported_files": 0,
                    "data_directory": data_directory
                }
            )
        
        file_analysis = []
        total_rows = 0
        all_columns = set()
        common_issues = []
        recommendations = []
        
        # 각 파일 분석
        for file_path in all_files:
            try:
                # 파일 읽기
                if file_path.endswith('.csv'):
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)
                
                # 파일 분석
                file_info = {
                    "file_name": os.path.basename(file_path),
                    "file_path": file_path,
                    "rows": len(df),
                    "columns": len(df.columns),
                    "column_names": df.columns.tolist(),
                    "missing_values": df.isnull().sum().to_dict(),
                    "data_types": df.dtypes.astype(str).to_dict(),
                    "file_size_mb": round(os.path.getsize(file_path) / (1024 * 1024), 2)
                }
                
                # 행 수 검증
                if len(df) < min_rows:
                    file_info["issues"] = [f"행 수가 부족합니다 (최소 {min_rows}행 필요, 현재 {len(df)}행)"]
                    common_issues.append(f"{os.path.basename(file_path)}: 행 수 부족")
                
                # 동적 컬럼 검증 (필수 컬럼이 지정된 경우에만)
                if required_columns and len(required_columns) > 0:
                    missing_columns = set(required_columns) - set(df.columns)
                    if missing_columns:
                        file_info["issues"] = file_info.get("issues", []) + [f"필수 컬럼 누락: {list(missing_columns)}"]
                        common_issues.append(f"{os.path.basename(file_path)}: 필수 컬럼 누락")
                else:
                    # 동적 분석: 데이터 구조 기반 품질 평가
                    if len(df.columns) < 3:
                        file_info["warnings"] = file_info.get("warnings", []) + ["컬럼 수가 적습니다 (최소 3개 권장)"]
                    if len(df) < 10:
                        file_info["warnings"] = file_info.get("warnings", []) + ["데이터 행 수가 적습니다 (최소 10행 권장)"]
                
                # 결측값 검증
                high_missing_cols = [col for col, missing in df.isnull().sum().items() if missing > len(df) * 0.5]
                if high_missing_cols:
                    file_info["warnings"] = [f"높은 결측값 비율: {high_missing_cols}"]
                
                file_analysis.append(file_info)
                total_rows += len(df)
                all_columns.update(df.columns)
                
            except Exception as e:
                file_analysis.append({
                    "file_name": os.path.basename(file_path),
                    "file_path": file_path,
                    "error": f"파일 읽기 오류: {str(e)}"
                })
                common_issues.append(f"{os.path.basename(file_path)}: 파일 읽기 오류")
        
        # 전체 데이터 품질 평가 (동적 기준)
        is_data_ready = len(common_issues) == 0 and total_rows >= min_rows
        
        # 동적 분석 모드: 필수 컬럼이 없으면 더 유연한 평가
        if not required_columns or len(required_columns) == 0:
            # 기본적인 데이터 품질만 확인
            is_data_ready = total_rows >= min_rows and len(all_files) > 0
        
        # 권장사항 생성 (동적 모드)
        if not is_data_ready:
            if total_rows < min_rows:
                recommendations.append(f"데이터 행 수를 {min_rows}행 이상으로 늘려주세요")
            if common_issues:
                recommendations.append("파일 형식과 구조를 확인하고 수정해주세요")
        else:
            # 동적 분석 모드에서 성공적인 경우
            if not required_columns or len(required_columns) == 0:
                recommendations.append("데이터가 준비되었습니다. 다양한 분석이 가능합니다.")
                recommendations.append("리포트 생성을 시작할 수 있습니다.")
        
        # 데이터 품질 개선 권장사항
        if len(all_files) > 1:
            # 여러 파일의 컬럼 일관성 확인
            column_consistency = {}
            for file_info in file_analysis:
                if "column_names" in file_info:
                    for col in file_info["column_names"]:
                        if col not in column_consistency:
                            column_consistency[col] = 0
                        column_consistency[col] += 1
            
            inconsistent_columns = [col for col, count in column_consistency.items() if count < len(all_files)]
            if inconsistent_columns:
                recommendations.append(f"컬럼 일관성 개선: {inconsistent_columns} 컬럼이 모든 파일에 없습니다")
        
        # 데이터 분석 가능성 평가 (동적 모드)
        if total_rows > 0 and is_data_ready:
            if not required_columns or len(required_columns) == 0:
                recommendations.append("데이터 구조를 분석하여 맞춤형 리포트를 생성할 수 있습니다.")
            else:
                recommendations.append("데이터가 준비되었습니다. 분석을 시작할 수 있습니다.")
        
        validation_summary = {
            "total_files": len(all_files),
            "supported_files": len([f for f in file_analysis if "error" not in f]),
            "total_rows": total_rows,
            "total_columns": len(all_columns),
            "data_directory": data_directory,
            "data_quality_score": max(0, 100 - len(common_issues) * 20)  # 간단한 품질 점수
        }
        
        return DataValidationOutput(
            success=True,
            is_data_ready=is_data_ready,
            validation_summary=validation_summary,
            file_analysis=file_analysis,
            issues=common_issues,
            recommendations=recommendations
        )
        
    except Exception as e:
        # 디버깅을 위한 상세 오류 정보
        error_details = f"데이터 검증 중 오류가 발생했습니다: {str(e)}"
        
        return DataValidationOutput(
            success=False,
            is_data_ready=False,
            error_message=error_details
        )


class DataValidationTool:
    def __init__(self):
        self.name = "validate_data"
        self.description = "사용자 데이터가 분석에 준비되어 있는지 검증합니다. 사용자가 '데이터 확인해줘' 등의 요청을 할 때 사용되며, 파일 존재, 형식, 구조, 품질을 종합적으로 확인하여 친근하게 결과를 제공합니다."
        self.input_model = DataValidationInput
        self.output_model = DataValidationOutput
        self.execute = validate_data
