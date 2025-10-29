# 이미지 경로 처리를 위한 핸들러 예시

## 개요
TorchServe의 핸들러에서 이미지 경로를 입력받고, 추론 결과를 커스터마이징하는 방법을 설명합니다.

## 핸들러 구조

### 기본 흐름
```
입력 요청 → preprocess() → inference() → postprocess() → 응답 반환
```

## 예시 1: 이미지 경로를 입력받아 처리

```python
# image_handler.py
import torch
from PIL import Image
from torchvision import transforms
from ts.torch_handler.base_handler import BaseHandler
import os

class ImagePathHandler(BaseHandler):
    def initialize(self, context):
        """모델 초기화 시 호출"""
        super().initialize(context)

        # 이미지 전처리 파이프라인 정의
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

    def preprocess(self, data):
        """
        입력: [{"body": {"image_path": "/path/to/image.jpg"}}]
        출력: 전처리된 텐서
        """
        images = []

        for row in data:
            # 요청 본문에서 이미지 경로 추출
            body = row.get("body")
            if isinstance(body, dict):
                image_path = body.get("image_path")
            else:
                # 바이트 스트림으로 받은 경우
                image_path = row.get("data") or row.get("body")

            # 이미지 로드
            if os.path.exists(image_path):
                image = Image.open(image_path).convert('RGB')
            else:
                raise ValueError(f"이미지를 찾을 수 없습니다: {image_path}")

            # 전처리 적용
            image_tensor = self.transform(image)
            images.append(image_tensor)

        # 배치로 결합
        return torch.stack(images)

    def inference(self, data):
        """모델 추론"""
        with torch.no_grad():
            predictions = self.model(data)
        return predictions

    def postprocess(self, inference_output):
        """
        추론 결과를 원하는 형태로 변환
        """
        # Softmax 적용
        probabilities = torch.nn.functional.softmax(inference_output, dim=1)

        # Top-5 예측 추출
        top5_prob, top5_catid = torch.topk(probabilities, 5)

        results = []
        for i in range(len(top5_prob)):
            result = {
                "predictions": [
                    {
                        "class_id": top5_catid[i][j].item(),
                        "probability": top5_prob[i][j].item()
                    }
                    for j in range(5)
                ]
            }
            results.append(result)

        return results
```

## 예시 2: 이미지 경로를 입력받고 결과를 파일로 저장

```python
# image_save_handler.py
import torch
from PIL import Image
from torchvision import transforms
from ts.torch_handler.base_handler import BaseHandler
import os
import json
from datetime import datetime

class ImageSaveHandler(BaseHandler):
    def initialize(self, context):
        super().initialize(context)

        # 결과 저장 디렉토리 설정
        self.output_dir = os.getenv("OUTPUT_DIR", "./outputs")
        os.makedirs(self.output_dir, exist_ok=True)

        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

    def preprocess(self, data):
        """이미지 경로에서 이미지 로드 및 전처리"""
        images = []
        self.image_paths = []  # 나중에 postprocess에서 사용

        for row in data:
            body = row.get("body", {})
            image_path = body.get("image_path")

            if not image_path or not os.path.exists(image_path):
                raise ValueError(f"유효하지 않은 이미지 경로: {image_path}")

            self.image_paths.append(image_path)

            # 이미지 로드 및 전처리
            image = Image.open(image_path).convert('RGB')
            image_tensor = self.transform(image)
            images.append(image_tensor)

        return torch.stack(images)

    def inference(self, data):
        """모델 추론"""
        with torch.no_grad():
            predictions = self.model(data)
        return predictions

    def postprocess(self, inference_output):
        """결과를 파일로 저장하고 경로 반환"""
        probabilities = torch.nn.functional.softmax(inference_output, dim=1)
        top5_prob, top5_catid = torch.topk(probabilities, 5)

        results = []

        for i, image_path in enumerate(self.image_paths):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"result_{timestamp}_{i}.json"
            output_path = os.path.join(self.output_dir, output_filename)

            # 결과 데이터
            result_data = {
                "input_image": image_path,
                "timestamp": timestamp,
                "predictions": [
                    {
                        "class_id": top5_catid[i][j].item(),
                        "probability": top5_prob[i][j].item()
                    }
                    for j in range(5)
                ]
            }

            # JSON 파일로 저장
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)

            results.append({
                "input_image": image_path,
                "output_file": output_path,
                "top_prediction": {
                    "class_id": top5_catid[i][0].item(),
                    "probability": top5_prob[i][0].item()
                }
            })

        return results
```

## 예시 3: Base64 인코딩된 이미지 또는 경로 둘 다 지원

```python
# flexible_image_handler.py
import torch
from PIL import Image
from torchvision import transforms
from ts.torch_handler.base_handler import BaseHandler
import os
import base64
from io import BytesIO

class FlexibleImageHandler(BaseHandler):
    def initialize(self, context):
        super().initialize(context)

        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

    def preprocess(self, data):
        """이미지 경로 또는 Base64 데이터 모두 처리"""
        images = []

        for row in data:
            body = row.get("body", {})

            # 케이스 1: 이미지 경로
            if "image_path" in body:
                image_path = body["image_path"]
                if not os.path.exists(image_path):
                    raise ValueError(f"이미지를 찾을 수 없습니다: {image_path}")
                image = Image.open(image_path).convert('RGB')

            # 케이스 2: Base64 인코딩된 이미지
            elif "image_base64" in body:
                image_data = base64.b64decode(body["image_base64"])
                image = Image.open(BytesIO(image_data)).convert('RGB')

            # 케이스 3: 바이너리 데이터
            elif "data" in row:
                image = Image.open(BytesIO(row["data"])).convert('RGB')

            else:
                raise ValueError("image_path, image_base64, 또는 data가 필요합니다")

            # 전처리 적용
            image_tensor = self.transform(image)
            images.append(image_tensor)

        return torch.stack(images)

    def inference(self, data):
        """모델 추론"""
        with torch.no_grad():
            predictions = self.model(data)
        return predictions

    def postprocess(self, inference_output):
        """결과 후처리"""
        probabilities = torch.nn.functional.softmax(inference_output, dim=1)
        top5_prob, top5_catid = torch.topk(probabilities, 5)

        results = []
        for i in range(len(top5_prob)):
            result = {
                "predictions": [
                    {
                        "class_id": top5_catid[i][j].item(),
                        "class_name": f"class_{top5_catid[i][j].item()}",
                        "probability": round(top5_prob[i][j].item(), 4)
                    }
                    for j in range(5)
                ]
            }
            results.append(result)

        return results
```

## 사용 예시

### 1. 이미지 경로로 요청
```bash
curl -X POST http://localhost:8080/predictions/my_model \
  -H "Content-Type: application/json" \
  -d '{
    "image_path": "/path/to/image.jpg"
  }'
```

### 2. Base64 이미지로 요청
```bash
# 이미지를 Base64로 인코딩
IMAGE_BASE64=$(base64 -i image.jpg)

curl -X POST http://localhost:8080/predictions/my_model \
  -H "Content-Type: application/json" \
  -d "{
    \"image_base64\": \"$IMAGE_BASE64\"
  }"
```

### 3. Python에서 호출
```python
import requests
import json

# 이미지 경로로 요청
response = requests.post(
    "http://localhost:8080/predictions/my_model",
    json={"image_path": "/path/to/image.jpg"}
)
result = response.json()
print(json.dumps(result, indent=2))

# Base64로 요청
import base64

with open("image.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

response = requests.post(
    "http://localhost:8080/predictions/my_model",
    json={"image_base64": image_data}
)
result = response.json()
print(json.dumps(result, indent=2))
```

## 핸들러 메서드 상세 설명

### initialize(context)
- 모델 로딩 시 한 번만 호출
- 전처리 파이프라인, 클래스 레이블 등 초기화
- context에서 모델 정보, 설정 등 접근 가능

### preprocess(data)
- **입력**: HTTP 요청 데이터 리스트
- **역할**: 원시 데이터를 모델 입력 형태로 변환
- **출력**: 모델이 처리할 수 있는 텐서

### inference(data)
- **입력**: preprocess의 출력
- **역할**: 모델 추론 실행
- **출력**: 모델의 원시 출력

### postprocess(data)
- **입력**: inference의 출력
- **역할**: 모델 출력을 사용자 친화적 형태로 변환
- **출력**: JSON 직렬화 가능한 결과

## 환경 변수 활용

핸들러에서 환경 변수를 사용하여 경로 등을 설정할 수 있습니다:

```python
import os

class ConfigurableHandler(BaseHandler):
    def initialize(self, context):
        super().initialize(context)

        # 환경 변수에서 설정 로드
        self.input_dir = os.getenv("INPUT_DIR", "./inputs")
        self.output_dir = os.getenv("OUTPUT_DIR", "./outputs")
        self.save_results = os.getenv("SAVE_RESULTS", "false").lower() == "true"
```

서버 시작 시:
```bash
export INPUT_DIR=/data/inputs
export OUTPUT_DIR=/data/outputs
export SAVE_RESULTS=true

torchserve --start \
  --model-store model_store \
  --models my_model=my_model.mar
```

## 요약

**핸들러의 역할:**
- `preprocess`: 입력 데이터 변환 (경로 → 이미지 → 텐서)
- `inference`: 모델 추론
- `postprocess`: 결과 형식 변환 (텐서 → JSON 응답)

**커스터마이징 포인트:**
- 입력 형식: 경로, Base64, 바이너리 등
- 전처리: 리사이즈, 정규화, augmentation 등
- 출력 형식: JSON, 파일 저장, 이미지 생성 등
