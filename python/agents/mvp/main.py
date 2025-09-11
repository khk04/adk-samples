from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
import shutil
from pathlib import Path
from typing import Optional
import json

from mvp_agent.agent import mvp_report_generator
from mvp_agent.config import DATA_DIR, REPORTS_DIR

app = FastAPI(title="MVP Report Generator", version="0.1.0")

# 정적 파일 서빙을 위한 디렉토리 설정
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """메인 페이지"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MVP Report Generator</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .upload-area { border: 2px dashed #ccc; padding: 20px; text-align: center; margin: 20px 0; }
            .btn { background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; }
            .btn:hover { background: #0056b3; }
            .result { margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 MVP Report Generator</h1>
            <p>CSV 데이터를 업로드하여 자동으로 비즈니스 리포트를 생성합니다.</p>
            
            <div class="upload-area">
                <h3>CSV 파일 업로드</h3>
                <form action="/upload" method="post" enctype="multipart/form-data">
                    <input type="file" name="file" accept=".csv" required>
                    <br><br>
                    <button type="submit" class="btn">리포트 생성 시작</button>
                </form>
            </div>
            
            <div>
                <h3>샘플 데이터로 테스트</h3>
                <a href="/generate-sample" class="btn">샘플 데이터로 리포트 생성</a>
            </div>
            
            <div>
                <h3>생성된 리포트</h3>
                <a href="/reports" class="btn">리포트 목록 보기</a>
            </div>
        </div>
    </body>
    </html>
    """

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """CSV 파일 업로드 및 리포트 생성"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="CSV 파일만 업로드 가능합니다.")
    
    # 업로드된 파일 저장
    file_path = DATA_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # 에이전트 실행 (비동기 처리 필요)
        # 실제 구현에서는 백그라운드 태스크로 처리하는 것이 좋습니다
        result = await run_agent_with_file(str(file_path))
        
        return {
            "message": "리포트 생성이 완료되었습니다.",
            "filename": file.filename,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"리포트 생성 중 오류 발생: {str(e)}")

@app.get("/generate-sample")
async def generate_sample_report():
    """샘플 데이터로 리포트 생성"""
    sample_file = DATA_DIR / "sample_sales_data.csv"
    
    if not sample_file.exists():
        raise HTTPException(status_code=404, detail="샘플 데이터 파일이 없습니다.")
    
    try:
        result = await run_agent_with_file(str(sample_file))
        return {
            "message": "샘플 데이터로 리포트 생성이 완료되었습니다.",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"리포트 생성 중 오류 발생: {str(e)}")

@app.get("/reports")
async def list_reports():
    """생성된 리포트 목록"""
    reports_dir = Path(REPORTS_DIR)
    if not reports_dir.exists():
        return {"reports": []}
    
    reports = []
    for file_path in reports_dir.glob("*.txt"):
        reports.append({
            "filename": file_path.name,
            "created_at": file_path.stat().st_mtime,
            "size": file_path.stat().st_size
        })
    
    # 생성 시간 순으로 정렬
    reports.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {"reports": reports}

@app.get("/reports/{filename}")
async def get_report(filename: str):
    """특정 리포트 내용 조회"""
    report_path = Path(REPORTS_DIR) / filename
    
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다.")
    
    return FileResponse(report_path, media_type="text/plain")

async def run_agent_with_file(csv_path: str):
    """에이전트 실행 (실제 구현에서는 ADK 에이전트 호출)"""
    # 실제 구현에서는 ADK 에이전트를 호출해야 합니다
    # 여기서는 시뮬레이션된 결과를 반환합니다
    return {
        "status": "success",
        "message": "리포트 생성 완료",
        "csv_path": csv_path,
        "note": "실제 구현에서는 ADK 에이전트가 실행됩니다."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)