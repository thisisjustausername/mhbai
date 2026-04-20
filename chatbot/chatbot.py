import faiss
import pickle
from ollama import Client

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

from sentence_transformers import SentenceTransformer

embed_model = SentenceTransformer("all-MiniLM-L6-v2", device="cuda:0")  # GPU


def retrieve_modules(query, k=15):
    q_vec = embed_model.encode([query]).astype("float32")
    faiss.normalize_L2(q_vec)  # if you used cosine similarity
    D, I = index.search(q_vec, k)
    return [modules[i] for i in I[0]]


def ask_llm(query, retrieved_modules):
    context = "\n---------------------------------------------\n".join(
        "\n".join(f"{key}: {value}" for key, value in m.items() if key != "score")
        for m in retrieved_modules
    )
    prompt = f"""
Du bist ein Antwortassistent für Module der Universität Augsburg.
Du darfst nur angegebene Module und Modulinformationen verwenden, um die Frage zu beantworten. Wenn die Informationen nicht ausreichen, um die Frage zu beantworten, antworte mit "Es tut mir leid, aber ich habe nicht genügend Informationen, um diese Frage zu beantworten." oder "Die bereitgestellten Informationen reichen nicht aus, um diese Frage zu beantworten." Verwende keine Informationen außerhalb der bereitgestellten Module. Antworte so genau wie möglich auf die Frage.
Dir stehen ausschließlich die Informationen der folgenden Module zur Verfügung. Entnehme nur Informationen aus diesen Modulen, um die Frage zu beantworten. Verwende keine Informationen außerhalb dieser Module. Antworte so genau wie möglich auf die Frage.
Hier sind relevante Module:
{context}
"""
    client = Client(
        # host="http://misit-183.informatik.uni-augsburg.de:11434/"
    )
    response = client.chat(
        model="llama3.2:1b",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": query},
        ],
        stream=False,
    )
    print(response["message"]["content"])


while True:
    query = input("Frage: ")
    top_modules = retrieve_modules(query, k=15)
    answer = ask_llm(query, top_modules)
    print("\nAntwort:\n", answer)

