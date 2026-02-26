from sentence_transformers import SentenceTransformer

# Load model once globally
model = SentenceTransformer("all-MiniLM-L6-v2")


def generate_embedding(text):
    """
    Generate embedding vector for given text.
    """
    return model.encode(text).tolist()