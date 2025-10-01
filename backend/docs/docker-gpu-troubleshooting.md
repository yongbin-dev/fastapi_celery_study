# Docker GPU 환경 구축 트러블슈팅

## 문제 요약

PaddlePaddle GPU 버전이 Docker 컨테이너 내에서 CUDA 라이브러리를 찾지 못하는 문제가 발생했습니다.

## 발생한 오류들

### 1. cuDNN 라이브러리를 찾지 못하는 오류

```
PreconditionNotMetError: Cannot load cudnn shared library. Cannot invoke method cudnnGetVersion.
[Hint: cudnn_dso_handle should not be null.]
```

**원인:**
- PaddlePaddle이 `/usr/local/cuda/lib64/libcudnn.so`를 찾음
- 실제로는 `/usr/lib/x86_64-linux-gnu/libcudnn.so.8`에 위치

**해결방법:**
```dockerfile
RUN mkdir -p /usr/local/cuda/lib64 \
    && ln -s /usr/lib/x86_64-linux-gnu/libcudnn.so.8 /usr/local/cuda/lib64/libcudnn.so
```

### 2. CUDA 라이브러리(libcublas.so) 경로 문제

```
PreconditionNotMetError: The third-party dynamic library (libcublas.so) that Paddle depends on is not configured correctly.
(error code is libcublas.so: cannot open shared object file: No such file or directory)
```

**원인:**
- CUDA 라이브러리가 `/usr/local/cuda-11.8/targets/x86_64-linux/lib/`에 위치
- `LD_LIBRARY_PATH`에 해당 경로가 포함되지 않음
- PaddlePaddle이 버전 번호 없는 `libcublas.so`를 찾지만, 실제로는 `libcublas.so.11`만 존재

**해결방법:**

1. **심볼릭 링크 생성 (Dockerfile):**
```dockerfile
RUN ln -s /usr/local/cuda-11.8/targets/x86_64-linux/lib/libcublas.so.11 \
          /usr/local/cuda-11.8/targets/x86_64-linux/lib/libcublas.so \
    && ln -s /usr/local/cuda-11.8/targets/x86_64-linux/lib/libcublasLt.so.11 \
          /usr/local/cuda-11.8/targets/x86_64-linux/lib/libcublasLt.so
```

2. **LD_LIBRARY_PATH 환경변수 설정 (docker-compose.yml):**
```yaml
environment:
  - LD_LIBRARY_PATH=/usr/local/cuda/lib64:/usr/local/cuda-11.8/targets/x86_64-linux/lib:/usr/lib/x86_64-linux-gnu:/usr/local/nvidia/lib:/usr/local/nvidia/lib64
  - CUDA_HOME=/usr/local/cuda-11.8
```

### 3. README.md 파일 누락으로 빌드 실패

```
OSError: Readme file does not exist: README.md
```

**원인:**
- `pyproject.toml`에서 README.md를 참조
- Docker 빌드 시 `uv sync` 실행 전에 README.md가 복사되지 않음

**해결방법:**
```dockerfile
# 의존성 파일과 함께 README.md 복사
COPY pyproject.toml uv.lock README.md ./

# 그 다음 uv sync 실행
RUN uv sync --extra prod --no-dev --no-cache
```

## 최종 해결 방법

### 1. Dockerfile.gpu 수정

```dockerfile
# CUDA 라이브러리 심볼릭 링크 생성
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl git \
    libglib2.0-0 libsm6 libxext6 libxrender1 libgomp1 libgl1 \
    python3-dev python3-pip \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /usr/local/cuda/lib64 \
    && ln -s /usr/lib/x86_64-linux-gnu/libcudnn.so.8 /usr/local/cuda/lib64/libcudnn.so \
    && ln -s /usr/local/cuda-11.8/targets/x86_64-linux/lib/libcublas.so.11 /usr/local/cuda-11.8/targets/x86_64-linux/lib/libcublas.so \
    && ln -s /usr/local/cuda-11.8/targets/x86_64-linux/lib/libcublasLt.so.11 /usr/local/cuda-11.8/targets/x86_64-linux/lib/libcublasLt.so

# README.md 포함하여 복사
COPY pyproject.toml uv.lock README.md ./
```

### 2. docker-compose.yml 수정

```yaml
environment:
  - LD_LIBRARY_PATH=/usr/local/cuda/lib64:/usr/local/cuda-11.8/targets/x86_64-linux/lib:/usr/lib/x86_64-linux-gnu:/usr/local/nvidia/lib:/usr/local/nvidia/lib64
  - CUDA_HOME=/usr/local/cuda-11.8
```

## 핵심 교훈

1. **베이스 이미지의 ENV가 최우선**: Dockerfile의 ENV 설정보다 베이스 이미지의 ENV가 우선되므로, docker-compose.yml에서 환경변수를 명시적으로 설정해야 함

2. **라이브러리 경로 불일치**: NVIDIA CUDA 베이스 이미지는 표준 경로와 다른 위치에 라이브러리를 설치하므로, 심볼릭 링크나 LD_LIBRARY_PATH 설정이 필수

3. **버전 번호가 있는 라이브러리**: `.so.11` 형태의 버전 번호가 있는 라이브러리만 존재하는 경우, 버전 없는 심볼릭 링크를 생성해야 함

4. **빌드 순서 중요**: Docker 빌드 시 파일 복사 순서가 중요하며, 특히 `pyproject.toml`에서 참조하는 파일은 먼저 복사되어야 함

## 검증 방법

```bash
# PaddlePaddle GPU 동작 확인
docker exec fastapi-app bash -c "uv run python -c 'import paddle; paddle.utils.run_check()'"

# 성공 메시지
# PaddlePaddle works well on 1 GPU.
# PaddlePaddle is installed successfully! Let's start deep learning with PaddlePaddle now.
```

## 참고 사항

- CUDA 버전: 11.8.0
- cuDNN 버전: 8
- 베이스 이미지: `nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu20.04`
- GPU Compute Capability: 8.9
- Driver API Version: 13.0
