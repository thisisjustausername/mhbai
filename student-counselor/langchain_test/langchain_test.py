import time

from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core._api.beta_decorator import LangChainBetaWarning
import warnings

from rich.markdown import Markdown
from rich.live import Live
from rich.console import Console
from rich import print as p

warnings.filterwarnings("ignore", category=LangChainBetaWarning)

embeddings = OllamaEmbeddings(model="qwen3-embedding")

db = Chroma(
            persist_directory=str("student-counselor/chroma_db"),
            embedding_function=embeddings,
        )


@tool
def query_academic_knowledgebase(query: str, k: int = 5) -> str:
    """
    Durchsucht die internen Informationskarten für Studiengängen nach Studiengangsinformationen, Inhalten, Zulassungsvoraussetzungen (NC) und weiteren studiengangsspezifischen Fragen.

    Args:
        query (str): Die Suchanfrage, die Informationen zu einem Studiengang oder studiengangsbezogenen Fragen enthält.
        k (int): Die Anzahl der zurückzugebenden relevanten Ergebnisse.
    
    Returns:
        str: Die relevantesten Informationen aus den Informationskarten, die der Anfrage entsprechen. Wenn keine relevanten Informationen gefunden werden, wird eine entsprechende Nachricht zurückgegeben.
    """
    matches = db.similarity_search(query, k=k)

    if not matches:
        return "Keine passenden Informationen gefunden."

    return "\n\n".join(
        [
            f"Treffer {index + 1}:\n"
            f"Studiengang: {match.metadata.get('Studiengang', 'unbekannt')}\n"
            f"Inhalt: {match.page_content}\n"
            f"Metadaten: {match.metadata}"
            for index, match in enumerate(matches)
        ]
    )


llm = ChatOllama(
    model="qwen3.6:35b", 
    temperature=0.5,
    num_predict=2048,  # Entspricht max_tokens in Ollama
)


system_prompt = """Du bist ein hochpräziser Assistent für die Studienberatung.
Nutze das Suchwerkzeug bei Fragen zu bestimmten Studiengängen, Bedingungen, oder Fragen, bei denen Informationen zu Studiengängen relevant sind. Du darfst kein eigenes Wissen verwenden, sondern nur das recherchierte Wissen anwenden.
Antworte auf Deutsch und in schönem Markdown-Format.
Auf Fragen, die nichts mit dem Studium zu tun haben, oder eine Meinung fordern, antworte mit 'Darüber habe ich leider keine Kenntnisse.'

Regeln:
    - Verwende das Suchwerkzeug, um Informationen zu Studiengängen zu finden
    - Antworte auf Deutsch und in schönem Markdown-Format
    - Entnehme dabei das Wissen aus der ANTWORT DES SEARCH-TOOLS
    - Gebe immer eine Antwort. Wenn du keine Informationen findest, teile dies in deiner Antwort mit.
    - Duze die Nutzer/in

Tools:
    - query_academic_knowledgebase: Durchsucht die internen Informationskarten für Studiengängen nach Studiengangsinformationen, Inhalten, Zulassungsvoraussetzungen (NC) und weiteren studiengangsspezifischen Fragen
"""

agent = create_agent(
    model=llm,
    tools=[query_academic_knowledgebase],
    system_prompt=system_prompt
)


query = "Welche Studiengänge haben mit Musik zu tun?"
query = input("Stelle Deine Frage:     ")
p(Markdown(f"**Anfrage:** {query}"))
print()
print("Hi, ich bin Hera, deine Studienberaterin.\n⌛ Ich suche mal nach einer Antwort...")

# result = agent.invoke(
#     {"messages": [{"role": "user", "content": query}]}
# )
# p(Markdown(result["messages"][-1].content_blocks[0]["text"]))

stream = agent.stream_events(
    {"messages": [{"role": "user", "content": query}]},
    version="v3"
)

console = Console()
accumulated_text = ""

with Live(Markdown(""), console=console, refresh_per_second=15) as live:
    for name, item in stream.interleave("messages", "tool_calls"):
        if name == "messages":
            if str(item.text) != "":
                print("🥳 Heureka, ich habe da was für Dich...")
                print("\n\n")
                p(Markdown("**Antwort:**"))

            for delta in item.text:
                accumulated_text += delta
                live.update(Markdown(accumulated_text))

        elif name == "tool_calls":
            if item.tool_name == "query_academic_knowledgebase":
                print(f"🔭 Suche nach einer Antwort irgendwo da draußen...")
                print(f"🧠 Lass mich kurz nachdenken...")