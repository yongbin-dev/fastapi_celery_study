# TorchServe 모델 아카이브 생성 가이드

## 개요
TorchServe에서 모델을 배포하기 위해 `.mar` (Model Archive) 파일을 생성하는 과정을 설명합니다.

## 필요한 파일

### 1. model.py - 모델 아키텍처 정의
```python
import torch
import torch.nn as nn

class SimpleModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(10, 2)

    def forward(self, x):
        return self.fc(x)
```

### 2. handler.py - 요청/응답 핸들러
```python
import torch
from ts.torch_handler.base_handler import BaseHandler

class MyHandler(BaseHandler):
    def preprocess(self, data):
        # 입력 데이터 전처리
        input_data = data[0].get("body")
        tensor = torch.tensor(input_data["data"])
        return tensor

    def inference(self, data):
        # 모델 추론
        with torch.no_grad():
            if self.model is None:
                return
            output = self.model(data)
        return output

    def postprocess(self, data):
        # 결과 후처리
        return [{"prediction": data.tolist()}]
```

### 3. resnet18.pth - 학습된 모델 가중치
모델의 `state_dict`를 저장한 파일입니다.

## 모델 아카이브 생성

### 명령어
```bash
torch-model-archiver \
  --model-name simple_model \
  --version 1.0 \
  --model-file model.py \
  --serialized-file resnet18.pth \
  --handler handler.py \
  --export-path model_store
```

### 파라미터 설명
- `--model-name`: 모델 이름 (서빙 시 사용될 이름)
- `--version`: 모델 버전
- `--model-file`: 모델 아키텍처 정의 파일
- `--serialized-file`: 학습된 모델 가중치 파일 (.pth)
- `--handler`: 커스텀 핸들러 파일
- `--export-path`: 생성된 .mar 파일을 저장할 디렉토리

### 생성 결과
```
model_store/
└── simple_model.mar (43.4 MB)
```

## TorchServe 실행

### 1. 서버 시작
```bash
torchserve --start \
  --model-store model_store \
  --models simple_model=simple_model.mar
```

### 2. 추론 테스트
```bash
curl -X POST http://localhost:8080/predictions/simple_model \
  -H "Content-Type: application/json" \
  -d '{
    "data": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
  }'
```

### 3. 모델 상태 확인
```bash
# 관리 API (기본 포트: 8081)
curl http://localhost:8081/models/simple_model

# 전체 모델 목록
curl http://localhost:8081/models
```

### 4. 서버 중지
```bash
torchserve --stop
```

## 주요 포트
- **8080**: 추론 API (Inference API)
- **8081**: 관리 API (Management API)
- **8082**: 메트릭 API (Metrics API)

## 추가 옵션

### 런타임 지정
```bash
torch-model-archiver \
  --model-name simple_model \
  --version 1.0 \
  --model-file model.py \
  --serialized-file resnet18.pth \
  --handler handler.py \
  --runtime python \
  --export-path model_store
```

### 추가 파일 포함
```bash
torch-model-archiver \
  --model-name simple_model \
  --version 1.0 \
  --model-file model.py \
  --serialized-file resnet18.pth \
  --handler handler.py \
  --extra-files index_to_name.json,config.yaml \
  --export-path model_store
```

### requirements 지정
```bash
torch-model-archiver \
  --model-name simple_model \
  --version 1.0 \
  --model-file model.py \
  --serialized-file resnet18.pth \
  --handler handler.py \
  --requirements-file requirements.txt \
  --export-path model_store
```

### 아카이브 형식 변경
```bash
torch-model-archiver \
  --model-name simple_model \
  --version 1.0 \
  --model-file model.py \
  --serialized-file resnet18.pth \
  --handler handler.py \
  --archive-format zip-store \
  --export-path model_store
```

## 문제 해결

### 오류: required arguments 누락
```
torch-model-archiver: error: the following arguments are required: --model-name, --handler, -v/--version
```
**해결**: 필수 파라미터 확인
- `--model-name`
- `--handler`
- `--version` (또는 `-v`)

### 오류: 파일을 찾을 수 없음
**해결**: 현재 디렉토리에 모든 파일이 있는지 확인
```bash
ls -la *.py *.pth
```

### 오류: 모델 로드 실패
**해결**: model.py의 클래스 이름과 serialized-file의 state_dict가 호환되는지 확인

## 참고사항
- `.mar` 파일은 모델 배포를 위한 패키지 형식입니다
- 하나의 `.mar` 파일에 모델 아키텍처, 가중치, 핸들러가 모두 포함됩니다
- 버전 관리를 통해 여러 버전의 모델을 동시에 서빙할 수 있습니다
- 핸들러를 커스터마이징하여 전처리/후처리 로직을 자유롭게 구현할 수 있습니다
