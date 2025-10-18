"""
ML Server Main Application
AI/ML 모델 추론을 담당하는 서버
"""

import sys

import uvicorn

sys.path.insert(0, ".")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
