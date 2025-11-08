# Pylance 오류 해결 가이드

gRPC generated 파일에서 발생하는 Pylance 오류를 완전히 해결하는 방법입니다.

---

## 🔧 적용된 해결책

### 1. VSCode 설정 추가 (`.vscode/settings.json`)

```json
{
  "python.analysis.exclude": [
    "**/grpc/generated/**",
    "**/__pycache__",
    "**/.venv"
  ],
  "python.analysis.ignore": [
    "**/grpc/generated/**"
  ],
  "python.linting.pylintArgs": [
    "--ignore=grpc/generated"
  ],
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true
  },
  "python.analysis.typeCheckingMode": "basic",
  "python.analysis.diagnosticSeverityOverrides": {
    "reportGeneralTypeIssues": "none",
    "reportOptionalMemberAccess": "none"
  }
}
```

**효과:**
- ✅ Pylance가 generated 폴더를 분석에서 제외
- ✅ 일반적인 타입 이슈 경고 억제
- ✅ __pycache__ 파일 숨김

---

### 2. Pyright 설정 수정 (`pyrightconfig.json`)

```json
{
  "exclude": [
    "**/__pycache__",
    "**/.venv",
    "**/node_modules"
  ],
  "ignore": [
    "**/grpc/generated/*_pb2.py",
    "**/grpc/generated/*_grpc.py"
  ]
}
```

**효과:**
- ✅ `.py` 파일은 타입 체크에서 제외
- ✅ `.pyi` 파일은 타입 힌트로 사용

---

### 3. Import 경로 수정 (`ocr_pb2.pyi`)

**변경 전:**
```python
import common_pb2 as _common_pb2  # ❌ 절대 import
```

**변경 후:**
```python
from . import common_pb2 as _common_pb2  # ✅ 상대 import
```

**효과:**
- ✅ 모듈을 올바르게 찾을 수 있음
- ✅ 패키지 내부 import 오류 해결

---

### 4. 타입 패키지 마커 추가 (`py.typed`)

**파일 위치:**
```
packages/shared/shared/grpc/generated/py.typed
```

**효과:**
- ✅ 이 패키지가 타입 정보를 제공한다고 명시
- ✅ Pylance가 `.pyi` 파일을 올바르게 인식

---

## 🔄 VSCode 리로드 방법

설정을 적용하려면 VSCode를 리로드해야 합니다.

### 방법 1: 명령 팔레트
1. `Ctrl+Shift+P` (macOS: `Cmd+Shift+P`)
2. "Developer: Reload Window" 입력
3. Enter

### 방법 2: 단축키
- Windows/Linux: `Ctrl+R`
- macOS: `Cmd+R`

### 방법 3: VSCode 재시작
- VSCode 완전히 종료 후 재실행

---

## ✅ 확인 방법

리로드 후 다음을 확인하세요:

### 1. Pylance 상태 확인
```python
# packages/ml_server/ml_app/grpc_services/ocr_service.py
from shared.grpc.generated import ocr_pb2, ocr_pb2_grpc  # 빨간 줄 없어야 함

request = ocr_pb2.OCRRequest(
    private_image_path="/test.jpg"  # 자동완성 작동해야 함
)
```

### 2. 타입 힌트 확인
- 변수에 마우스 오버 시 타입 정보가 표시되어야 함
- 자동완성이 정상 작동해야 함

### 3. Problems 탭 확인
- VSCode 하단의 "Problems" 탭에서 오류 개수 확인
- gRPC generated 관련 오류가 사라져야 함

---

## 🐛 여전히 오류가 발생하는 경우

### A. Pylance 서버 재시작

1. `Ctrl+Shift+P` → "Python: Restart Language Server"
2. 또는 VSCode 완전 재시작

### B. Python 인터프리터 재선택

1. `Ctrl+Shift+P` → "Python: Select Interpreter"
2. `.venv` 가상환경 선택
3. 정확한 경로: `./venv/bin/python`

### C. 캐시 삭제

```bash
# Pylance 캐시 삭제
rm -rf ~/.vscode/extensions/ms-python.vscode-pylance-*/dist/bundled/stubs
rm -rf .vscode/.ropeproject

# 프로젝트 캐시 삭제
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

### D. 타입 체크 모드 조정

`.vscode/settings.json`에서:

```json
{
  "python.analysis.typeCheckingMode": "off"  // 완전히 끄기
}
```

또는

```json
{
  "python.analysis.typeCheckingMode": "basic"  // 기본 모드
}
```

---

## 📝 문제별 해결 방법

### 문제 1: "Cannot find module 'common_pb2'"

**원인:** Import 경로 문제

**해결:**
```python
# ocr_pb2.pyi 수정
from . import common_pb2 as _common_pb2  # 상대 import 사용
```

### 문제 2: "Stub file not found"

**원인:** `.pyi` 파일이 인식되지 않음

**해결:**
```bash
# py.typed 파일 생성
touch packages/shared/shared/grpc/generated/py.typed
```

### 문제 3: 자동완성 작동 안 함

**원인:** Pylance가 타입 정보를 읽지 못함

**해결:**
1. VSCode 리로드
2. Python 인터프리터 재선택
3. Pylance 서버 재시작

### 문제 4: 여전히 빨간 줄 표시

**원인:** Pylance 캐시 문제

**해결:**
```bash
# 캐시 삭제 후 VSCode 재시작
rm -rf ~/.vscode/extensions/ms-python.vscode-pylance-*/
```

---

## 🎯 최종 검증

모든 설정이 올바르게 적용되었는지 확인:

### 체크리스트

- [ ] `.vscode/settings.json` 파일 존재
- [ ] `pyrightconfig.json`에 ignore 설정
- [ ] `ocr_pb2.pyi`에 상대 import 사용
- [ ] `py.typed` 파일 존재
- [ ] VSCode 리로드 완료
- [ ] Pylance 서버 재시작
- [ ] Problems 탭에 gRPC 관련 오류 없음
- [ ] 자동완성 정상 작동
- [ ] 타입 힌트 표시됨

### 테스트 코드

```python
# test_pylance.py
from shared.grpc.generated import ocr_pb2, common_pb2

# 자동완성 테스트
request = ocr_pb2.OCRRequest(
    private_image_path="/test.jpg",  # 자동완성 작동해야 함
    language="korean",
    confidence_threshold=0.5
)

# 타입 체크 테스트
status: common_pb2.Status = common_pb2.STATUS_SUCCESS  # 오류 없어야 함

# 응답 객체 테스트
response = ocr_pb2.OCRResponse(
    status=common_pb2.STATUS_SUCCESS,
    text="테스트",
    overall_confidence=0.95
)
```

**기대 결과:**
- ✅ 빨간 줄 없음
- ✅ 자동완성 작동
- ✅ 타입 힌트 표시
- ✅ Problems 탭에 오류 없음

---

## 📚 참고 자료

- [Pylance 설정 문서](https://github.com/microsoft/pylance-release)
- [Pyright 설정 문서](https://github.com/microsoft/pyright/blob/main/docs/configuration.md)
- [PEP 561 - 타입 힌트 패키지](https://www.python.org/dev/peps/pep-0561/)

---

**작성일:** 2025-11-08
**최종 업데이트:** 2025-11-08
