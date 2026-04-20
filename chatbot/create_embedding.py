from sentence_transformers import SentenceTransformer

def embed_texts(data: list[dict[str, str | int | None]]) -> list[list[float]]:
    """
    Creates embeddings for a list of module dictionaries.

    Args:
        data (list[dict[str, str | int | None]]): A list of dictionaries containing module information.

    Returns:
        list[list[float]]: A list of embedding vectors.
    """
    text_data = ["\n\n".join(f"{key}: {value}" for key, value in d.items() if key != "score") for d in data]
    
    model = SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2",
        device="cuda:0"
    )
    embeddings = model.encode(text_data, batch_size=64, show_progress_bar=True)
    return embeddings