# model.py
import torch
import torch.nn as nn

class SimpleModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(10, 2)
    
    def forward(self, x):
        return self.fc(x)

# 모델 저장
model = SimpleModel()
torch.save(model.state_dict(), 'resnet18.pth')