import json
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings


embeddings = OllamaEmbeddings(model="qwen3-embedding")

with open("student-counselor/info-cards.json", "r") as f:
    info_cards = json.load(f)

docs = []

for entry in info_cards:
    name = entry[0]["Name"]
    
    metadata ={"Studiengang": entry[0]['Name'], 
                "Abschluss": entry[0]['Studienabschluss'],
                "Zulassungsmodus": entry[0]['Zulassungsmodus'],
                "Unterrichtssprache": entry[0]['Unterrichtssprache'],
                "Studienbeginn": entry[0]['Studienbeginn'],
                "Deutschkenntnisse": entry[0]['Deutschkenntnisse (Mindestanforderungen)'],
                "Inhalt": entry[0]['content'],
                "Perspektiven": ', '.join(entry[0]['perspectives'])
    }
    if (d := entry[0].get('Regelstudienzeit', None)) is not None:
        metadata["Regelstudienzeit"] = d
    if (d := entry[0].get('Studienform', None)) is not None:
        metadata["Studienform"] = d
    if entry[0]['Zulassungsmodus'].strip().lower() != 'zulassungsfrei':
        if (d := ' / '.join([e for e in ['Wintersemester: ' + entry[0].get('Bewerbungsschluss Wintersemester', ''), 'Sommersemester: ' + entry[0].get('Bewerbungsschluss Sommersemester', '')] if e not in ["Wintersemester: ", "Sommersemester: "]])) != '':
            metadata["Bewerbungsfrist"] = d

    doc = Document(
        page_content=entry[1],
        metadata=metadata
    )
    docs.append(doc)

vector_store = Chroma.from_documents(
    documents=docs,
    embedding=embeddings,
    persist_directory="student-counselor/chroma_db"
)