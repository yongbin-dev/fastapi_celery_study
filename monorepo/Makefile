# FastAPI + Celery + ML 모노레포 Makefile
# Docker 빌드 및 관리 자동화

.PHONY: help build build-all build-api build-celery build-ml-base build-ml-ocr \
        up down restart logs clean prune dev prod health test

# 기본 변수
DOCKER_COMPOSE := docker-compose
PROJECT_NAME := fastapi-celery-study
REGISTRY := # Docker registry URL (필요시 설정)

# 이미지 태그
TAG ?= latest
API_IMAGE := $(PROJECT_NAME)-api:$(TAG)
CELERY_IMAGE := $(PROJECT_NAME)-celery:$(TAG)
ML_BASE_IMAGE := backend-ml-base:$(TAG)
ML_BASE_CPU_IMAGE := backend-ml-base-cpu:$(TAG)
ML_OCR_IMAGE := $(PROJECT_NAME)-ml-ocr:$(TAG)

# 도움말
help:
	@echo "======================================"
	@echo "FastAPI + Celery + ML 모노레포 Make 명령어"
	@echo "======================================"
	@echo ""
	@echo "빌드 명령어:"
	@echo "  make build-all        - 모든 서비스 이미지 빌드"
	@echo "  make build-api        - API 서버 이미지 빌드"
	@echo "  make build-celery     - Celery Worker 이미지 빌드"
	@echo "  make build-ml-base    - ML Base 이미지 빌드 (GPU)"
	@echo "  make build-ml-base-cpu - ML Base 이미지 빌드 (CPU)"
	@echo "  make build-ml-ocr     - ML OCR 이미지 빌드 (ml-base 필요)"
	@echo ""
	@echo "실행 명령어:"
	@echo "  make up               - 모든 서비스 시작"
	@echo "  make down             - 모든 서비스 중지"
	@echo "  make restart          - 모든 서비스 재시작"
	@echo "  make logs             - 로그 확인 (tail -f)"
	@echo "  make logs-api         - API 서버 로그만 확인"
	@echo "  make logs-celery      - Celery Worker 로그만 확인"
	@echo "  make logs-ml          - ML 서버 로그만 확인"
	@echo ""
	@echo "관리 명령어:"
	@echo "  make health           - 서비스 상태 확인"
	@echo "  make clean            - 중지된 컨테이너 및 사용하지 않는 이미지 정리"
	@echo "  make prune            - 모든 미사용 Docker 리소스 정리 (주의!)"
	@echo "  make rebuild          - 캐시 없이 전체 재빌드"
	@echo ""
	@echo "개발/배포:"
	@echo "  make dev              - 개발 환경 시작 (.env.development)"
	@echo "  make prod             - 프로덕션 환경 시작 (.env)"
	@echo "  make test             - 테스트 환경 빌드 및 실행"
	@echo ""
	@echo "옵션:"
	@echo "  TAG=v1.0.0 make build-all  - 특정 태그로 빌드"
	@echo ""

# 전체 빌드
build-all: build-ml-base build-api build-celery build-ml-ocr
	@echo "✅ 모든 이미지 빌드 완료"

# API 서버 빌드
build-api:
	@echo "🔨 API 서버 이미지 빌드 중..."
	cd packages && docker build \
		-f api_server/Dockerfile \
		-t $(API_IMAGE) \
		--build-arg BUILDKIT_INLINE_CACHE=1 \
		.
	@echo "✅ API 서버 이미지 빌드 완료: $(API_IMAGE)"

# Celery Worker 빌드
build-celery:
	@echo "🔨 Celery Worker 이미지 빌드 중..."
	cd packages && docker build \
		-f celery_worker/Dockerfile \
		-t $(CELERY_IMAGE) \
		--build-arg BUILDKIT_INLINE_CACHE=1 \
		.
	@echo "✅ Celery Worker 이미지 빌드 완료: $(CELERY_IMAGE)"

# ML Base 이미지 빌드 (GPU 버전)
build-ml-base:
	@echo "🔨 ML Base (GPU) 이미지 빌드 중..."
	@if [ -f packages/ml_server/Dockerfile.base ]; then \
		cd packages && docker build \
			-f ml_server/Dockerfile.base \
			-t $(ML_BASE_IMAGE) \
			--build-arg BUILDKIT_INLINE_CACHE=1 \
			.; \
	else \
		echo "⚠️  Dockerfile.base not found, skipping ml-base build"; \
	fi
	@echo "✅ ML Base (GPU) 이미지 빌드 완료: $(ML_BASE_IMAGE)"

# ML Base CPU 이미지 빌드 (CPU 버전)
build-ml-base-cpu:
	@echo "🔨 ML Base (CPU) 이미지 빌드 중..."
	@if [ -f packages/ml_server/Dockerfile.base.cpu ]; then \
		cd packages && docker build \
			-f ml_server/Dockerfile.base.cpu \
			-t $(ML_BASE_CPU_IMAGE) \
			--build-arg BUILDKIT_INLINE_CACHE=1 \
			.; \
	else \
		echo "⚠️  Dockerfile.base.cpu not found, skipping ml-base-cpu build"; \
	fi
	@echo "✅ ML Base (CPU) 이미지 빌드 완료: $(ML_BASE_CPU_IMAGE)"

# ML OCR 이미지 빌드 (ml-base-cpu 기반)
build-ml-ocr: build-ml-base-cpu
	@echo "🔨 ML OCR (CPU) 이미지 빌드 중..."
	cd packages && docker build \
		-f ml_server/Dockerfile \
		-t $(ML_OCR_IMAGE) \
		--build-arg BUILDKIT_INLINE_CACHE=1 \
		.
	@echo "✅ ML OCR (CPU) 이미지 빌드 완료: $(ML_OCR_IMAGE)"

# 캐시 없이 재빌드
rebuild:
	@echo "🔨 캐시 없이 전체 재빌드 중..."
	cd packages && docker build --no-cache -f api_server/Dockerfile -t $(API_IMAGE) .
	cd packages && docker build --no-cache -f celery_worker/Dockerfile -t $(CELERY_IMAGE) .
	@if [ -f packages/ml_server/Dockerfile.base ]; then \
		cd packages && docker build --no-cache -f ml_server/Dockerfile.base -t $(ML_BASE_IMAGE) .; \
	fi
	cd packages && docker build --no-cache -f ml_server/Dockerfile -t $(ML_OCR_IMAGE) .
	@echo "✅ 전체 재빌드 완료"

# Docker Compose 명령어 (docker-compose.yml이 있다고 가정)
up:
	@if [ -f docker-compose.yml ]; then \
		echo "🚀 서비스 시작 중..."; \
		$(DOCKER_COMPOSE) up -d; \
		echo "✅ 서비스 시작 완료"; \
	else \
		echo "⚠️  docker-compose.yml not found"; \
	fi

down:
	@if [ -f docker-compose.yml ]; then \
		echo "🛑 서비스 중지 중..."; \
		$(DOCKER_COMPOSE) down; \
		echo "✅ 서비스 중지 완료"; \
	else \
		echo "⚠️  docker-compose.yml not found"; \
	fi

restart: down up

# 로그 확인
logs:
	@if [ -f docker-compose.yml ]; then \
		$(DOCKER_COMPOSE) logs -f; \
	else \
		echo "⚠️  docker-compose.yml not found"; \
	fi

logs-api:
	@if [ -f docker-compose.yml ]; then \
		$(DOCKER_COMPOSE) logs -f api_server; \
	else \
		echo "⚠️  docker-compose.yml not found"; \
	fi

logs-celery:
	@if [ -f docker-compose.yml ]; then \
		$(DOCKER_COMPOSE) logs -f celery_worker; \
	else \
		echo "⚠️  docker-compose.yml not found"; \
	fi

logs-ml:
	@if [ -f docker-compose.yml ]; then \
		$(DOCKER_COMPOSE) logs -f ml_server; \
	else \
		echo "⚠️  docker-compose.yml not found"; \
	fi

# 서비스 상태 확인
health:
	@echo "🔍 서비스 상태 확인 중..."
	@if [ -f docker-compose.yml ]; then \
		$(DOCKER_COMPOSE) ps; \
	else \
		docker ps --filter "name=$(PROJECT_NAME)"; \
	fi

# 정리 명령어
clean:
	@echo "🧹 중지된 컨테이너 및 미사용 이미지 정리 중..."
	docker container prune -f
	docker image prune -f
	@echo "✅ 정리 완료"

prune:
	@echo "⚠️  모든 미사용 Docker 리소스를 정리합니다 (컨테이너, 네트워크, 이미지, 볼륨)"
	@read -p "계속하시겠습니까? [y/N] " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		docker system prune -a --volumes -f; \
		echo "✅ 정리 완료"; \
	else \
		echo "❌ 취소됨"; \
	fi

# 개발/프로덕션 환경
dev:
	@if [ -f docker-compose.yml ]; then \
		echo "🚀 개발 환경 시작 중..."; \
		$(DOCKER_COMPOSE) --env-file .env.development up -d; \
		echo "✅ 개발 환경 시작 완료"; \
	else \
		echo "⚠️  docker-compose.yml not found"; \
	fi

prod:
	@if [ -f docker-compose.yml ]; then \
		echo "🚀 프로덕션 환경 시작 중..."; \
		$(DOCKER_COMPOSE) --env-file .env up -d; \
		echo "✅ 프로덕션 환경 시작 완료"; \
	else \
		echo "⚠️  docker-compose.yml not found"; \
	fi

# 테스트 환경
test: build-all
	@echo "🧪 테스트 환경 실행 중..."
	@if [ -f docker-compose.test.yml ]; then \
		$(DOCKER_COMPOSE) -f docker-compose.test.yml up --abort-on-container-exit; \
		$(DOCKER_COMPOSE) -f docker-compose.test.yml down; \
	else \
		echo "⚠️  docker-compose.test.yml not found"; \
	fi

# 이미지 푸시 (레지스트리 설정 필요)
push:
	@if [ -z "$(REGISTRY)" ]; then \
		echo "⚠️  REGISTRY 변수가 설정되지 않았습니다"; \
		echo "예: make push REGISTRY=myregistry.com"; \
		exit 1; \
	fi
	@echo "📤 이미지 푸시 중..."
	docker tag $(API_IMAGE) $(REGISTRY)/$(API_IMAGE)
	docker tag $(CELERY_IMAGE) $(REGISTRY)/$(CELERY_IMAGE)
	docker tag $(ML_OCR_IMAGE) $(REGISTRY)/$(ML_OCR_IMAGE)
	docker push $(REGISTRY)/$(API_IMAGE)
	docker push $(REGISTRY)/$(CELERY_IMAGE)
	docker push $(REGISTRY)/$(ML_OCR_IMAGE)
	@echo "✅ 이미지 푸시 완료"

# 버전 정보 출력
version:
	@echo "프로젝트: $(PROJECT_NAME)"
	@echo "태그: $(TAG)"
	@echo ""
	@echo "이미지:"
	@echo "  - API: $(API_IMAGE)"
	@echo "  - Celery: $(CELERY_IMAGE)"
	@echo "  - ML Base: $(ML_BASE_IMAGE)"
	@echo "  - ML OCR: $(ML_OCR_IMAGE)"
