from tools.desktop import CURRENT_MODEL


class LLMBridge:

    def __init__(self):
        self.model = CURRENT_MODEL

    def set_model(self, model):
        self.model = model
        print(f"LLMBridge-Model: {self.model}")

