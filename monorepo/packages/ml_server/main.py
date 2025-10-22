"""
ML Server Main Application
AI/ML 모델 추론을 담당하는 서버
"""

import uvicorn

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("ml_app.main:app", host="0.0.0.0", port=8000, reload=True)
