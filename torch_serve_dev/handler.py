# handler.py
import torch
from ts.torch_handler.base_handler import BaseHandler



class MyHandler(BaseHandler):
    def preprocess(self, data):
        # 입력 데이터 전처리
        input_data = data[0].get("body")
        tensor = torch.tensor(input_data["data"])
        return tensor
    
    def inference(self, data):
        # 모델 추론
        with torch.no_grad():
            if self.model is None:
                return
            output = self.model(data)
            
        return output
    
    def postprocess(self, data):
        # 결과 후처리
        return [{"prediction": data.tolist()}]