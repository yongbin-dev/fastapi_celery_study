# packages/shared/Makefile
# gRPC Proto 컴파일 스크립트

.PHONY: generate-grpc clean-grpc help

help:
	@echo "사용 가능한 명령어:"
	@echo "  make generate-grpc  - Proto 파일에서 Python 코드 생성"
	@echo "  make clean-grpc     - 생성된 gRPC 파일 삭제"

generate-grpc:
	@echo "🔨 gRPC 코드 생성 시작..."
	python -m grpc_tools.protoc \
		-I./shared/grpc/protos \
		--python_out=./shared/grpc/generated \
		--grpc_python_out=./shared/grpc/generated \
		--pyi_out=./shared/grpc/generated \
		./shared/grpc/protos/*.proto

	@echo "📝 __init__.py 생성..."
	touch ./shared/grpc/generated/__init__.py

	@echo "✅ gRPC 코드 생성 완료!"
	@echo ""
	@echo "생성된 파일:"
	@ls -lh ./shared/grpc/generated/

clean-grpc:
	@echo "🗑️  생성된 gRPC 파일 삭제..."
	rm -rf ./shared/grpc/generated/*.py
	rm -rf ./shared/grpc/generated/*.pyi
	@echo "✅ 삭제 완료!"
