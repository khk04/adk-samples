"""사용자 데이터 확인 요청 도구"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from google.adk.tools.function_tool import FunctionTool
import os
from ..config import VDATA_DIR, DEFAULT_REQUIRED_COLUMNS


class UserDataCheckInput(BaseModel):
    """사용자 데이터 확인 요청 입력"""
    user_request: str = Field(..., description="사용자의 데이터 확인 요청 내용")
    data_directory: str = Field(default="data/generated_sales_data", description="기본 데이터 디렉토리 경로")


class UserDataCheckOutput(BaseModel):
    """사용자 데이터 확인 요청 출력"""
    success: bool = Field(..., description="요청 처리 성공 여부")
    message: str = Field(..., description="사용자에게 보여줄 메시지")
    should_validate: bool = Field(..., description="데이터 검증을 수행해야 하는지 여부")
    validation_params: Dict[str, Any] = Field(default_factory=dict, description="데이터 검증에 필요한 매개변수")


@FunctionTool
def check_user_data_request(user_request: str = "데이터 확인해줘", data_directory: Optional[str] = None) -> UserDataCheckOutput:
    """
    사용자의 데이터 확인 요청을 분석하고 적절한 응답을 제공합니다.
    
    이 도구는 사용자가 다음과 같은 요청을 할 때 사용됩니다:
    - "데이터 확인해줘"
    - "내 데이터가 준비되어 있어?"
    - "데이터 상태를 확인해줘"
    - "리포트를 만들어줘"
    - "분석을 시작해줘"
    
    사용자의 요청을 분석하여 데이터 검증이 필요한지 판단하고,
    필요한 경우 DataValidationTool을 사용하도록 안내합니다.
    """
    try:
        # 매개변수 기본값 설정 (config 사용)
        if data_directory is None:
            data_directory = str(VDATA_DIR)
        
        user_request = user_request.lower().strip()
        
        # 데이터 확인 관련 키워드
        data_check_keywords = [
            "데이터 확인", "데이터 상태", "데이터 준비", "데이터 검증",
            "내 데이터", "데이터가", "확인해줘", "상태를", "준비되어"
        ]
        
        # 리포트/분석 관련 키워드
        report_keywords = [
            "리포트", "분석", "보고서", "만들어줘", "생성", "시작", "작성", "기반으로"
        ]
        
        # 데이터 확인 요청인지 판단
        is_data_check_request = any(keyword in user_request for keyword in data_check_keywords)
        is_report_request = any(keyword in user_request for keyword in report_keywords)
        
        if is_data_check_request:
            # 직접적인 데이터 확인 요청
            message = f"네, 데이터 상태를 확인해드리겠습니다!\n\n현재 '{data_directory}' 디렉토리의 데이터를 검증하겠습니다."
            should_validate = True
            validation_params = {
                "data_directory": data_directory,
                "required_columns": DEFAULT_REQUIRED_COLUMNS,
                "min_rows": 10
            }
            
        elif is_report_request:
            # 리포트 생성 요청
            message = f"리포트 생성을 도와드리겠습니다!\n\nvdata 폴더의 데이터를 사용하여 6단계 질의를 통해 맞춤형 리포트를 생성하겠습니다."
            should_validate = True
            validation_params = {
                "data_directory": data_directory,
                "required_columns": DEFAULT_REQUIRED_COLUMNS,
                "min_rows": 10
            }
            
        else:
            # 일반적인 요청
            message = "안녕하세요!\n\n저는 vdata 폴더의 데이터를 분석하여 최적의 리포트를 생성하는 에이전트입니다.\n\n다음과 같은 요청을 도와드릴 수 있습니다:\n• 데이터 확인: '데이터 확인해줘'\n• 리포트 생성: '데이터를 기반으로 리포트를 작성해 주세요'\n• 분석 시작: '분석을 시작해줘'"
            should_validate = False
            validation_params = {}
        
        return UserDataCheckOutput(
            success=True,
            message=message,
            should_validate=should_validate,
            validation_params=validation_params
        )
        
    except Exception as e:
        return UserDataCheckOutput(
            success=False,
            message=f"요청을 처리하는 중 오류가 발생했습니다: {str(e)}",
            should_validate=False,
            validation_params={}
        )


class UserDataCheckTool:
    def __init__(self):
        self.name = "check_user_data_request"
        self.description = "사용자의 데이터 확인 요청을 분석하고 적절한 응답을 제공합니다. '데이터 확인해줘', '리포트를 만들어줘' 등의 요청을 처리합니다."
        self.input_model = UserDataCheckInput
        self.output_model = UserDataCheckOutput
        self.execute = check_user_data_request
