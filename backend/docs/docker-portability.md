# Docker 빌드 이식성 가이드

## 현재 설정의 이식성 분석

### ✅ 이식 가능한 부분

#### 1. Dockerfile.gpu
- **베이스 이미지**: `nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu20.04` - 고정 버전, 어디서나 동일
- **시스템 패키지**: apt-get으로 설치, 플랫폼 독립적
- **심볼릭 링크**: 절대 경로 사용하지만 컨테이너 내부 경로이므로 문제없음
- **Python 의존성**: uv + uv.lock으로 고정, 재현 가능

#### 2. docker-compose.yml (backend)
```yaml
environment:
  - LD_LIBRARY_PATH=/usr/local/cuda/lib64:/usr/local/cuda-11.8/targets/x86_64-linux/lib:/usr/lib/x86_64-linux-gnu:/usr/local/nvidia/lib:/usr/local/nvidia/lib64
  - CUDA_HOME=/usr/local/cuda-11.8
```
- 컨테이너 내부 경로만 사용, 이식 가능

### ⚠️ 주의가 필요한 부분

#### 1. GPU 드라이버 호환성

**요구사항:**
- NVIDIA GPU 필수
- NVIDIA Docker Runtime 설치 필요
- CUDA Driver >= 11.8 호환

**다른 PC에서 확인 사항:**
```bash
# GPU 확인
nvidia-smi

# Docker GPU 런타임 확인
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu20.04 nvidia-smi
```

#### 2. Docker Compose GPU 설정

현재 docker-compose.yml:
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

**문제점:**
- GPU가 없는 환경에서는 실패
- Docker Desktop (Mac)에서는 NVIDIA GPU 미지원

**해결방법:**
CPU/GPU 분리된 docker-compose 파일 사용 권장

#### 3. 네트워크 설정

```yaml
networks:
  app-network:
    external: true
```

**주의사항:**
- `app-network`를 미리 생성해야 함
- 다른 PC에서 첫 실행 시:
```bash
docker network create app-network
```

### ❌ 수정이 필요했던 부분 (이미 수정됨)

#### ~~1. 절대 경로 사용~~ (수정 완료)

**이전 (문제):**
```yaml
volumes:
  - /Users/aipim/yb/python/fastapi_celery_study/postgres_data:/var/lib/postgresql/data
```

**수정 후:**
```yaml
volumes:
  - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
    driver: local
```

## 다른 PC에서 빌드 시 체크리스트

### 1. 사전 요구사항 확인

```bash
# 1. Docker 설치 확인
docker --version

# 2. Docker Compose 설치 확인
docker-compose --version

# 3. NVIDIA GPU 및 드라이버 확인
nvidia-smi

# 4. NVIDIA Docker Runtime 설치 확인
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu20.04 nvidia-smi
```

### 2. 네트워크 생성

```bash
docker network create app-network
```

### 3. 빌드 및 실행

```bash
# 인프라 서비스 시작
cd infra
docker-compose up -d

# 애플리케이션 빌드 및 시작
cd ..
DOCKERFILE=Dockerfile.gpu docker-compose up --build -d
```

### 4. 검증

```bash
# 컨테이너 상태 확인
docker ps

# GPU 인식 확인
docker exec fastapi-app bash -c "uv run python -c 'import paddle; paddle.utils.run_check()'"

# 애플리케이션 접속
curl http://localhost:35050/docs
```

## 플랫폼별 제약사항

### Linux (Ubuntu/Debian)
- ✅ 모든 기능 완벽 지원
- NVIDIA GPU + Driver만 있으면 문제없음

### Windows (WSL2)
- ✅ WSL2 + NVIDIA CUDA on WSL 지원
- Docker Desktop for Windows에서 GPU 패스스루 지원
- **주의**: Windows 경로 구분자 차이 (자동 처리됨)

### macOS
- ❌ NVIDIA GPU 미지원 (Apple Silicon, Intel 모두)
- CPU 버전 사용 필요:
```bash
DOCKERFILE=Dockerfile.cpu docker-compose up -d
```

## 환경별 설정 분리 (권장)

### docker-compose.gpu.yml 생성
```yaml
version: "3.8"

services:
  app:
    extends:
      file: docker-compose.yml
      service: app
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

### docker-compose.cpu.yml 생성
```yaml
version: "3.8"

services:
  app:
    extends:
      file: docker-compose.yml
      service: app
    environment:
      - FLAGS_use_gpu=False
```

### 사용법
```bash
# GPU 환경
docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d

# CPU 환경
docker-compose -f docker-compose.yml -f docker-compose.cpu.yml up -d
```

## 빌드 캐시 최적화

### 레이어 캐싱 최대화

현재 Dockerfile은 이미 최적화되어 있음:
1. 시스템 패키지 (자주 변경 안 됨)
2. uv 설치 (자주 변경 안 됨)
3. pyproject.toml, uv.lock (의존성 변경 시에만)
4. 소스 코드 (자주 변경됨)

### 멀티 스테이지 빌드 (선택사항)

더 작은 이미지를 위한 멀티 스테이지:
```dockerfile
# 빌드 스테이지
FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu20.04 as builder
# ... 빌드 작업 ...

# 런타임 스테이지
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu20.04
COPY --from=builder /app /app
```

## 문제 해결

### "no matching manifest" 에러
**원인**: ARM 아키텍처 (Apple Silicon 등)에서 x86_64 이미지 사용 시도

**해결**:
```bash
# 플랫폼 명시
docker build --platform linux/amd64 -t backend-app .
```

### "could not select device driver"
**원인**: NVIDIA Docker Runtime 미설치

**해결**:
```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

## 결론

**현재 설정의 이식성: ✅ 양호**

- Dockerfile과 docker-compose는 상대 경로와 Docker 네임드 볼륨 사용
- CUDA 라이브러리 경로는 컨테이너 내부 절대 경로 (문제없음)
- NVIDIA GPU가 있는 Linux/WSL2 환경이면 어디서나 동일하게 빌드 및 실행 가능
- macOS는 CPU 버전만 가능

**다른 PC에서 빌드 시 필요한 것:**
1. Docker + Docker Compose
2. NVIDIA GPU + Driver (GPU 사용 시)
3. NVIDIA Docker Runtime (GPU 사용 시)
4. `docker network create app-network` 실행
