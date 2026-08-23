'''
Demonstrates a StateGraph workflow that augments a ChatOllama model with a
search tool backed by a Chroma vector store. This example is async and uses
streaming to print incremental model output.
'''


import asyncio
import operator
import warnings
from typing import Annotated, Literal

from dotenv import load_dotenv
from langchain.messages import AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langchain.tools import tool
from langchain_chroma import Chroma
from langchain_core._api.beta_decorator import LangChainBetaWarning
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langgraph.graph import END, START, StateGraph
from pymongo import MongoClient
from rich import print as p
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from typing_extensions import TypedDict

warnings.filterwarnings('ignore', category=LangChainBetaWarning)


################################################################
'''
Initialize vector database and model
'''
################################################################

embeddings = OllamaEmbeddings(model='qwen3-embedding')
db = Chroma(
            persist_directory='student-counselor/chroma_db',
            embedding_function=embeddings,
        )

model = ChatOllama(
    model='qwen3.6:35b',
    temperature=0.5,
    num_predict=4096,
    streaming=True
)

load_dotenv()  # Load environment variables from .env file

# %% Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/', authSource='unia', username='unia-search-ai', password=os.getenv('MONGO_DB_UNIA_SEARCH_AI_PASSWORD'))
db = client['unia']
mhbs = db['mhbs']
modules = db['modules']
exams = db['exams']


################################################################
'''
Create tools
'''
################################################################

@tool
async def search_studiengang(query: str, k: int = 5) -> str:
    '''
    Durchsucht die internen Informationskarten für Studiengängen nach Studiengangsinformationen, Inhalten, Zulassungsvoraussetzungen (NC) und weiteren studiengangsspezifischen Fragen.
    Du kannst immer nur nach EINEM Studiengang pro Anfrage suchen. Für mehrere Studiengänge stelle mehrere Anfragen. Stelle die Anfragen NACHEINANDER, sonst treten Fehler auf. Sende immer nur eine Suchanfrage und warte auf die Antwort bevor du die nächste Anfrage sendest.
    Du kannst folgende Bereiche zur Suche verwenden:
        * Studiengangsname
        * Inhalt
        * Berufsperspektiven
        * Ziele
        * Regelstudienzeit
        * Teil- / Vollzeitstudium
        * Zulassungsmodus
        * Studienbeginn
        * Unterrichtssprache
        * gefordertes Deutschniveau
    Es wird empfohlen, den Studiengangsnamen zu suchen, je nach Anfrage können auch die anderen Bereiche abgefragt werden.

    Args:
        query (str): Die Suchanfrage, die Informationen zu einem Studiengang oder studiengangsbezogenen Fragen enthält.
        k (int): Die Anzahl der zurückzugebenden relevanten Ergebnisse.

    Returns:
        str: Die relevantesten Informationen aus den Informationskarten, die der Anfrage entsprechen. Wenn keine relevanten Informationen gefunden werden, wird eine entsprechende Nachricht zurückgegeben.
    '''
    matches = db.similarity_search(query, k=k)

    if not matches:
        return 'Keine passenden Informationen gefunden.'

    return '\n\n'.join(
        [
            f'Treffer {index + 1}:\n'
            f'Studiengang: {match.metadata.get('Studiengang', 'unbekannt')}\n'
            f'Inhalt: {match.page_content}\n'
            f'Metadaten: {match.metadata}'
            for index, match in enumerate(matches)
        ]
    )


@tool
async def get_studiengang_modulhandbuch(studiengang: str, k: int = 5) -> str:
    '''
    Gibt das Modulhandbuch für einen bestimmten Studiengang zurück.

    Args:
        studiengang (str): Der Name des Studiengangs, für den das Modulhandbuch abgerufen werden soll.
        k (int): Die Anzahl der zurückzugebenden relevanten Ergebnisse.
    Returns:
        str: Das Modulhandbuch des angegebenen Studiengangs. Wenn kein Modulhandbuch gefunden wird, wird eine entsprechende Nachricht zurückgegeben.
    '''
    raise NotImplementedError('Diese Funktion ist noch nicht implementiert.')

################################################################
'''
Create workflow
'''
################################################################

class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int


# Augment the LLM with tools
tools = [search_studiengang]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)


system_prompt = '''Du bist ein hochpräziser Assistent für die Studienberatung.
Nutze das Suchwerkzeug bei Fragen zu bestimmten Studiengängen, Bedingungen, oder Fragen, bei denen Informationen zu Studiengängen relevant sind. Du darfst kein eigenes Wissen verwenden, sondern nur das recherchierte Wissen anwenden.
Antworte auf Deutsch und in schönem Markdown-Format.
Auf Fragen, die nichts mit dem Studium zu tun haben, oder eine Meinung fordern, antworte mit 'Darüber habe ich leider keine Kenntnisse.'

Regeln:
    - Verwende das Suchwerkzeug, um Informationen zu Studiengängen zu finden
    - Antworte auf Deutsch und in schönem Markdown-Format
    - Führe die Tools nur NACHEINANDER aus, nicht gleichzeitig. Warte auf die Antwort des Tools, bevor du das nächste Tool aufrufst.
    - Entnehme dabei das Wissen aus der ANTWORT DES SEARCH-TOOLS
    - Gebe immer eine Antwort. Wenn du keine Informationen findest, teile dies in deiner Antwort mit.
    - Duze die Nutzer/in

Tools:
    - search_studiengang: Durchsucht die internen Informationskarten für Studiengängen nach Studiengangsinformationen, Inhalten, Zulassungsvoraussetzungen (NC) und weiteren studiengangsspezifischen Fragen
        Du kannst folgende Bereiche zur Suche verwenden:
            * Studiengangsname
            * Inhalt
            * Berufsperspektiven
            * Ziele
            * Regelstudienzeit
            * Teil- / Vollzeitstudium
            * Zulassungsmodus
            * Studienbeginn
            * Unterrichtssprache
            * gefordertes Deutschniveau
        Es wird empfohlen, NUR DEN STUDIENGANGSNAMEN im Query zu suchen, je nach Anfrage können auch die anderen Bereiche abgefragt werden.
    - get_studiengang_modulhandbuch: Gibt das Modulhandbuch für einen bestimmten Studiengang zurück.
'''


# model node: decides whether to call the tool node
async def llm_call(state: dict):
    '''LLM decides whether to call a tool or not'''

    return {
        'messages': [
            await model_with_tools.ainvoke(
                [
                    SystemMessage(
                        content=system_prompt
                    )
                ]
                + state['messages']
            )
        ],
        'llm_calls': state.get('llm_calls', 0) + 1
    }


async def tool_node(state: dict):
    '''Performs the tool call'''

    result = []
    for tool_call in state['messages'][-1].tool_calls:
        tool = tools_by_name[tool_call['name']]
        observation = await tool.ainvoke(tool_call['args'])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call['id']))
    return {'messages': result}


async def should_continue(state: MessagesState) -> Literal['tool_node', END]:
    '''Decide if we should continue the loop or stop based upon whether the LLM made a tool call'''

    messages = state['messages']
    last_message = messages[-1]

    # If the LLM makes a tool call, then perform an action
    if last_message.tool_calls:
        return 'tool_node'

    # Otherwise, we stop (reply to the user)
    return END


################################################################
'''
Build agent
'''
################################################################

# Build workflow
agent_builder = StateGraph(MessagesState)

# Add nodes
agent_builder.add_node('llm_call', llm_call)
agent_builder.add_node('tool_node', tool_node)

# Add edges to connect nodes
agent_builder.add_edge(START, 'llm_call')
agent_builder.add_conditional_edges(
    'llm_call',
    should_continue,
    ['tool_node', END]
)
agent_builder.add_edge('tool_node', 'llm_call')

# Compile the agent
agent = agent_builder.compile()

# Show the agent
# with open('agent.png', 'wb') as f:
#     f.write(agent.get_graph(xray=True).draw_mermaid_png())

query = 'Wie unterscheiden sich die Studiengänge Data Science und Informatik'


# Invoke
# messages = [HumanMessage(content=query)]
# messages = agent.invoke({'messages': messages}) # type: ignore
# for m in messages['messages']:
#     print(m)

# stream =

def get_info(event) -> dict[str, str | None]:
    info = {}
    start = event.get('params', {}).get('data', ({},))
    if isinstance(start, tuple) and len(start) > 0:
        a = start[0].get('content', {})
        b = start[0].get('delta', {})
        info['type'] =  (a or b or {}).get('type', None)
        info['content'] = (a or b or {}).get('text', None)
        info['event'] = start[0].get('event', None)
    else:
       info['type'] = None
       info['content'] = None
       info['event'] = None
    return info



async def main():
    console = Console()
    accumulated_text = ''
    status = False
    run = await agent.astream_events(
            {'messages': [HumanMessage(content=query)]},
            version='v3'
        )
    print('🧠 Lass mich kurz nachdenken...')
    with Live(Markdown(''), console=console, refresh_per_second=15) as live:
        async for event in run:
            # Filter for the actual chat model streaming event
            res = get_info(event)
            if res['type'] == 'tool_call':
                print(f'🛠️ Tool-Aufruf {event['params']['data'][0]['content']['name']}: {a if not 'query' in (a := event['params']['data'][0]['content']['args']) else a['query']}')
            if res['type'] in ['text', 'text-delta'] and event['params']['data'][1]['langgraph_path'][1] == 'llm_call' and res['event'] != 'content-block-finish':
                if status is False:
                    print()
                status = True
                accumulated_text += res['content'] if res['content'] is not None else ''
                live.update(Markdown(accumulated_text))


if __name__ == '__main__':
    asyncio.run(main())
