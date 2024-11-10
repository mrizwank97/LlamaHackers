import ollama
import numpy as np

class OllamaEmbeddingFunction:
    def __init__(self, config):
        self.config = config
        self.model = self.config.EMBEDDING.MODEL

    def __call__(self, input):
        """
        Fetches embeddings for a single input or a list of inputs using the Ollama model.
        """
        if isinstance(input, str):
            return np.array(ollama.embeddings(model=self.model, prompt=input)["embedding"])
        elif isinstance(input, list):
            return [np.array(ollama.embeddings(model=self.model, prompt=item)["embedding"]) for item in input]
        else:
            raise ValueError("OllamaEmbeddingFunction expects a string or a list of strings as input.")
            