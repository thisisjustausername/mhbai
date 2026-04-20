import faiss
import pickle
from sentence_transformers import SentenceTransformer
import torch
from transformers import AutoTokenizer, AutoModelForQuestionAnswering

model_name  = "deepset/gelectra-base-germanquad"

embed_model = SentenceTransformer("all-MiniLM-L6-v2", device="cuda:0")  # GPU


translate_keys = {
    "module_code": "Modulcode",
    "title": "Titel",
    "ects": "ECTS",
    "complete_content": "Vollständiger Inhalt",
    "summarized_content": "Zusammenfassung des Inhalts",
    "goals": "Ziele",
    "summarized_goals": "Zusammenfassung der Ziele",
    "requirements": "Anforderungen",
    "recommended_semester": "Empfohlenes Semester",
    "module_parts": "Modulteile",
    "weekly_hours": "Wöchentliche Stunden",
    "expense": "Kosten",
    "exams": "Prüfungen",
    "success_requirements": "Erfolgsvoraussetzungen",
    "lecturer": "Dozent",
    "version": "Version",
}

index = faiss.read_index("modules.index")
with open("modules.pkl", "rb") as f:
    modules = pickle.load(f)
    modules = [
        {translate_keys.get(key, key): value for key, value in m.items()}
        for m in modules
    ]

def retrieve_modules(query, k=15):
    q_vec = embed_model.encode([query]).astype("float32")
    faiss.normalize_L2(q_vec)  # if you used cosine similarity
    _, I = index.search(q_vec, k)
    return [modules[i] for i in I[0]]


tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForQuestionAnswering.from_pretrained(model_name)

def ask_bert(query, retrieved_modules):
    best_score = -float("inf")
    context = "\n---------------------------------------------\n".join(
        "\n".join(f"{key}: {value}" for key, value in m.items() if key != "score")
        for m in retrieved_modules
    )
    inputs = tokenizer(query, context, truncation=True, max_length=512, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)

    # start and end logits
    start_logits = outputs.start_logits
    end_logits = outputs.end_logits

    # get most probable start and end token positions
    start_idx = torch.argmax(start_logits)
    end_idx = torch.argmax(end_logits) + 1  # +1 because slicing is exclusive

    answer_tokens = inputs['input_ids'][0][start_idx:end_idx]
    answer = tokenizer.decode(answer_tokens, skip_special_tokens=True)

    score = outputs.start_logits[0][start_idx] + outputs.end_logits[0][end_idx-1]
        
    if score > best_score:
        best_score = score
    
    return answer.strip(), score

while True:
    query = input("Frage: ")
    top_modules = retrieve_modules(query, k=15)
    answer, score = ask_bert(query, top_modules)
    print("\nAntwort:\n", answer)
    print("Score:\n", score)