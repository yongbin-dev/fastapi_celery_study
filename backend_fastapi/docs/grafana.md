# Grafana 대시보드 추가:

시나리오 1: DCGM 대시보드(ID: 14574)만 가져와서 사용하면 됩니다.
시나리오 2: DCGM 대시보드(ID: 14574)와 함께 Node Exporter Full 대시보드(ID: 1860)를 모두 가져와서 사용하면 시스템 전반과 GPU 상태를 모두 확인할 수 있습니다.

# docker-gpu 확인

NVIDIA Container Toolkit 설치
Docker 컨테이너가 GPU를 인식하고 사용할 수 있도록 NVIDIA Container Toolkit을 설치해야 합니다. 이 툴킷은 Docker 데몬과 NVIDIA 드라이버를 연결하는 역할을 합니다.

Ubuntu/Debian 기반 시스템:

### NVIDIA Container Toolkit GPG 키 추가

```sh
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
```

### NVIDIA Container Toolkit 저장소 추가

```sh
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
 sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
 sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
```

### 패키지 목록 업데이트

sudo apt-get update

### NVIDIA Container Toolkit 설치

```sh
sudo apt-get install -y nvidia-container-toolkit
```

설치 후 Docker 설정: Docker가 NVIDIA Container Runtime을 기본 런타임으로 사용하도록 설정해야 합니다.

Bash

### Docker 데몬 설정

```sh
sudo nvidia-ctk runtime configure --runtime=docker
```

### Docker 데몬 재시작

```sh
sudo systemctl restart docker
```

3. Docker GPU 연동 테스트
   위 단계들을 완료했다면, 이제 GPU가 Docker 컨테이너에서 제대로 작동하는지 테스트해볼 수 있습니다.

Bash

```sh
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
```
