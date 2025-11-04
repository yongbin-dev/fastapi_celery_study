#!/bin/bash
# gRPC 테스트 명령어 모음 (grpcurl 사용)
#
# 사용 전 grpcurl 설치 필요:
#   macOS: brew install grpcurl
#   Linux: https://github.com/fullstorydev/grpcurl/releases

SERVER="localhost:50051"

echo "🔧 gRPC OCR 서비스 테스트 명령어"
echo "=================================="
echo ""

# 색상 코드
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 1. 서비스 목록 확인
echo -e "${BLUE}1. 서비스 목록 확인${NC}"
echo "grpcurl -plaintext $SERVER list"
echo ""
grpcurl -plaintext $SERVER list
echo ""

# 2. OCRService 메서드 확인
echo -e "${BLUE}2. OCRService 메서드 확인${NC}"
echo "grpcurl -plaintext $SERVER list ocr.OCRService"
echo ""
grpcurl -plaintext $SERVER list ocr.OCRService
echo ""

# 3. 헬스 체크
echo -e "${BLUE}3. 헬스 체크${NC}"
echo "grpcurl -plaintext -d '{}' $SERVER ocr.OCRService/CheckHealth"
echo ""
grpcurl -plaintext -d '{}' $SERVER ocr.OCRService/CheckHealth
echo ""

# 4. OCR 텍스트 추출 (단일 이미지)
echo -e "${BLUE}4. OCR 텍스트 추출${NC}"
cat << 'EOF'
grpcurl -plaintext -d '{
  "public_image_path": "/http_test/sample.jpg",
  "private_image_path": "/http_data/sample.jpg",
  "language": "korean",
  "confidence_threshold": 0.5,
  "use_angle_cls": true
}' localhost:50051 ocr.OCRService/ExtractText
EOF
echo ""

# 5. 배치 OCR (스트리밍)
echo -e "${BLUE}5. 배치 OCR (스트리밍)${NC}"
cat << 'EOF'
grpcurl -plaintext -d '{
  "image_paths": [
    {"public_path": "/test/1.jpg", "private_path": "/data/1.jpg"},
    {"public_path": "/test/2.jpg", "private_path": "/data/2.jpg"}
  ],
  "language": "korean",
  "confidence_threshold": 0.5,
  "use_angle_cls": true
}' localhost:50051 ocr.OCRService/ExtractTextBatch
EOF
echo ""

# 6. Proto 정의 보기
echo -e "${BLUE}6. Proto 정의 보기${NC}"
echo "grpcurl -plaintext $SERVER describe ocr.OCRService"
echo ""

# 7. 메시지 타입 확인
echo -e "${BLUE}7. 메시지 타입 확인${NC}"
echo "grpcurl -plaintext $SERVER describe ocr.OCRRequest"
echo ""

echo -e "${GREEN}=================================="
echo "테스트 완료!"
echo "==================================${NC}"
