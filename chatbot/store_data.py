import faiss
import numpy as np
import pickle
from chatbot.fetch_data import fetch_data
from chatbot.create_embedding import embed_texts

data = fetch_data()
embeddings = embed_texts(data)

embeddings = np.array(embeddings).astype("float32")
faiss.normalize_L2(embeddings)  # if you want to use cosine similarity
index = faiss.IndexFlatIP(embeddings.shape[1])
index.add(embeddings)

# Save index
faiss.write_index(index, "modules.index")

# Save metadata (your JSONs)
with open("modules.pkl", "wb") as f:
    pickle.dump(data, f)