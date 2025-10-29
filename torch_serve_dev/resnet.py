from torchvision.models import resnet18, ResNet18_Weights
import torch

# pretrained 모델 다운로드
model = resnet18(weights=ResNet18_Weights.DEFAULT)
model.eval()

# 저장
torch.save(model.state_dict(), 'resnet18.pth')

# 또는 전체 모델 저장
torch.save(model, 'resnet18_full.pth')