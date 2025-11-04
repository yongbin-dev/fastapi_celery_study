#!/usr/bin/env python3
"""gRPC OCR 서비스 테스트 스크립트

사용법:
    python grpc_test.py health
    python grpc_test.py extract
    python grpc_test.py batch
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent / "packages" / "shared"))
sys.path.insert(0, str(Path(__file__).parent / "packages" / "celery_worker"))

import grpc
from shared.grpc.generated import common_pb2, ocr_pb2, ocr_pb2_grpc


class GrpcTester:
    """gRPC 테스트 클라이언트"""

    def __init__(self, server_address: str = "localhost:50051"):
        self.server_address = server_address
        self.channel = None
        self.stub = None

    async def connect(self):
        """gRPC 서버 연결"""
        self.channel = grpc.aio.insecure_channel(
            self.server_address,
            options=[
                ('grpc.max_send_message_length', 100 * 1024 * 1024),
                ('grpc.max_receive_message_length', 100 * 1024 * 1024),
            ]
        )
        self.stub = ocr_pb2_grpc.OCRServiceStub(self.channel)
        print(f"✅ 연결됨: {self.server_address}")

    async def close(self):
        """연결 종료"""
        if self.channel:
            await self.channel.close()
            print("🔌 연결 종료")

    async def test_health(self):
        """헬스 체크 테스트"""
        print("\n=== 헬스 체크 테스트 ===")

        request = ocr_pb2.HealthCheckRequest(
            service_name="OCRService"
        )

        try:
            if self.stub is None :
                raise Exception("self.stub is None")

            response = await self.stub.CheckHealth(request)

            print(f"📊 상태: {common_pb2.Status.Name(response.status)}")
            print(f"🔧 엔진: {response.engine_type}")
            print(f"✓ 모델 로드: {response.model_loaded}")
            print(f"📌 버전: {response.version}")

            return response.status == common_pb2.STATUS_SUCCESS

        except grpc.RpcError as e:
            print(f"❌ 오류: {e.code()} - {e.details()}")
            return False

    async def test_extract_text(
        self,
        private_path: str = "/data/test.jpg",
        public_path: str = "/test/test.jpg"
    ):
        """OCR 텍스트 추출 테스트"""
        print("\n=== OCR 텍스트 추출 테스트 ===")
        print(f"📂 이미지: {private_path}")

        request = ocr_pb2.OCRRequest(
            public_image_path=public_path,
            private_image_path=private_path,
            language="korean",
            confidence_threshold=0.5,
            use_angle_cls=True
        )

        try:
            if self.stub is None :
                raise Exception()

            response = await self.stub.ExtractText(request)

            print(f"\n📊 상태: {common_pb2.Status.Name(response.status)}")
            print(f"📝 전체 텍스트: {response.text[:100]}...")
            print(f"🎯 전체 신뢰도: {response.overall_confidence:.2f}")
            print(f"📦 텍스트 박스 수: {len(response.text_boxes)}")

            # 텍스트 박스 상세 정보
            for idx, box in enumerate(response.text_boxes[:5]):  # 최대 5개만 표시
                print(f"\n  [{idx + 1}] 텍스트: {box.text}")
                print(f"      신뢰도: {box.confidence:.2f}")
                print(f"      좌표: {list(box.bbox.coordinates)[:4]}...")

            if len(response.text_boxes) > 5:
                print(f"\n  ... 외 {len(response.text_boxes) - 5}개")

            # 메타데이터
            if response.metadata.data:
                print("📋 메타데이터:")
                for key, value in response.metadata.data.items():
                    print(f"  - {key}: {value}")

            # 에러 확인
            if response.status == common_pb2.STATUS_FAILURE:
                print("❌ 에러:")
                print(f"  코드: {response.error.code}")
                print(f"  메시지: {response.error.message}")
                print(f"  상세: {response.error.details}")

            return response.status == common_pb2.STATUS_SUCCESS

        except grpc.RpcError as e:
            print(f"❌ gRPC 오류: {e.code()} - {e.details()}")
            return False

    async def test_batch_extract(
        self,
        image_paths: Optional[list[tuple[str, str]]] = None
    ):
        """배치 OCR 테스트 (Server Streaming)"""
        print("\n=== 배치 OCR 테스트 ===")

        if image_paths is None:
            image_paths = [
                ("/data/test1.jpg", "/test/test1.jpg"),
                ("/data/test2.jpg", "/test/test2.jpg"),
                ("/data/test3.jpg", "/test/test3.jpg"),
            ]

        print(f"📂 이미지 수: {len(image_paths)}")

        # 요청 생성
        paths = [
            ocr_pb2.ImagePath(private_path=priv, public_path=pub)
            for priv, pub in image_paths
        ]

        request = ocr_pb2.OCRBatchRequest(
            image_paths=paths,
            language="korean",
            confidence_threshold=0.5,
            use_angle_cls=True
        )

        try:
            if self.stub is None :
                raise Exception()
            # 스트리밍 응답 수신
            async for progress in self.stub.ExtractTextBatch(request):
                print(f"\n📊 진행률: {progress.progress_percentage:.1f}%")
                print(f"   처리: {progress.processed_images}/{progress.total_images}")

                # 현재 결과
                result = progress.current_result
                print(f"   상태: {common_pb2.Status.Name(result.status)}")
                print(f"   텍스트 박스: {len(result.text_boxes)}개")
                print(f"   신뢰도: {result.overall_confidence:.2f}")

            print("\n✅ 배치 처리 완료!")
            return True

        except grpc.RpcError as e:
            print(f"❌ gRPC 오류: {e.code()} - {e.details()}")
            return False


async def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="gRPC OCR 테스트")
    parser.add_argument(
        "command",
        choices=["health", "extract", "batch", "all"],
        help="실행할 테스트"
    )
    parser.add_argument(
        "--server",
        default="localhost:50051",
        help="gRPC 서버 주소 (기본값: localhost:50051)"
    )
    parser.add_argument(
        "--image",
        default="/data/test.jpg",
        help="테스트 이미지 경로"
    )

    args = parser.parse_args()

    tester = GrpcTester(args.server)

    try:
        await tester.connect()

        if args.command == "health":
            await tester.test_health()

        elif args.command == "extract":
            await tester.test_extract_text(
                private_path=args.image,
                public_path="/test/test.jpg"
            )

        elif args.command == "batch":
            await tester.test_batch_extract()

        elif args.command == "all":
            print("🚀 전체 테스트 시작\n")
            success = True

            success &= await tester.test_health()
            success &= await tester.test_extract_text()
            success &= await tester.test_batch_extract()

            print("\n" + "=" * 50)
            if success:
                print("✅ 모든 테스트 통과!")
            else:
                print("❌ 일부 테스트 실패")
            print("=" * 50)

    except Exception as e:
        print(f"❌ 예외 발생: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())
