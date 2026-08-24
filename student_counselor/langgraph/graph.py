'''
Demonstrates a StateGraph workflow that augments a ChatOllama model with a
search tool backed by a Chroma vector store. This example is async and uses
streaming to print incremental model output.

Run using: chainlit run student_counselor/langgraph/graph.py --host 127.0.0.1 --port 8000
'''


import operator
import os
import re
import warnings
from typing import Annotated, Literal
from urllib.parse import urljoin

import chainlit as cl
import httpx
import trafilatura
from dotenv import load_dotenv
from langchain.messages import AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langchain.tools import tool
from langchain_chroma import Chroma
from langchain_core._api.beta_decorator import LangChainBetaWarning
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langgraph.graph import END, START, StateGraph
from pymongo import MongoClient
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
            persist_directory='student_counselor/chroma_db',
            embedding_function=embeddings,
        )

model = ChatOllama(
    model='qwen3.8:27b',
    temperature=0.5,
    num_predict=4096,
    streaming=True
)

load_dotenv()  # Load environment variables from .env file

# %% Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/', authSource='unia', username='unia-search-ai', password=os.getenv('MONGO_DB_UNIA_SEARCH_AI_PASSWORD'))
mongo_db = client['unia']
mhbs = mongo_db['mhbs']
modules = mongo_db['modules']
exams = mongo_db['exams']


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
    Du kannst mit und nach Infos in folgenden Bereichen suchen:
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
        str: Die relevantesten Informationen aus den Informationskarten, die der Anfrage entsprechen. Wenn keine relevanten Informationen gefunden werden, wird eine entsprechende Nachricht zurückgegeben. Es sind IMMER Informationen zu Studiengangsname, Inhalt, Berufsperspektiven, Ziele, Regelstudienzeit, Teil- / Vollzeitstudium, Zulassungsmodus, Studienbeginn, Unterrichtssprache, gefordertes Deutschniveau enthalten.
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


# NOTE: search_field Literal options originate from embedding_ fields in mongo_db/create_collection.py
@tool
async def get_studiengang_modulhandbuch(query: str, search_field: Literal['module_handbook', 'description', 'faculties', 'name', 'path'], k: int = 5, include_module_und_klausuren: bool = True) -> str:
    '''
    Gibt das Modulhandbuch für einen bestimmten Studiengang zurück.

    Args:
        studiengang (str): Der Name des Studiengangs, für den das Modulhandbuch abgerufen werden soll.
        k (int): Die Anzahl der zurückzugebenden relevanten Ergebnisse.
        include_module_und_klausuren (bool): Gibt an, ob Module und Klausuren in das Modulhandbuch einbezogen werden sollen. Falls False werden nur die IDs angegeben. Diese reichen NICHT, um Module zu vergleichen.
    Returns:
        str: Das Modulhandbuch des angegebenen Studiengangs. Wenn kein Modulhandbuch gefunden wird, wird eine entsprechende Nachricht zurückgegeben.
    '''
    if search_field not in ['module_handbook', 'description', 'faculties', 'name', 'path']:
        return f'Fehler: Ungültiger Parameter "{search_field}" für <search_field>. Bitte wähle eines der folgenden Felder: "module_handbook", "description", "faculties", "name", "path".'
    if search_field == 'module_handbook':
        search_field = 'embedding' # type: ignore



# TODO: add filters either in new function or in get_studiengang_modulhandbuch

@tool
async def get_modul(modul_name: str, k: int = 5) -> str:
    '''
    Gibt Informationen zu einem bestimmten Modul zurück.

    Args:
        modul_name (str): Der Name des Moduls, für das Informationen abgerufen werden sollen.
        k (int): Die Anzahl der zurückzugebenden relevanten Ergebnisse.
    Returns:
        str: Informationen zum angegebenen Modul. Wenn keine Informationen gefunden werden, wird eine entsprechende Nachricht zurückgegeben.
    '''
    raise NotImplementedError('Diese Funktion ist noch nicht implementiert.')


'''@tool
async def get_klausur():
    raise NotImplementedError('Diese Funktion ist noch nicht implementiert.')'''


def replacer(match):
    label, url = match.group(1), match.group(2)
    absolute = urljoin('https://www.uni-augsburg.de', url)
    return f'URL to {label}: {absolute}'


# TODO: use search engine to search for query then only allow uni augsburg links in the found urls or specify site: but that changes results to the worse
@tool
async def suche_uni_augsburg_website(url: str = 'https://www.uni-augsburg.de') -> str:
    '''
    Durchsucht die Website der Universität Augsburg nach Informationen zu Studiengängen, Modulen und Klausuren.

    Args:
        url (str): Die URL der Website, die durchsucht werden soll.
    Returns:
        str: Die gefundenen Informationen von der Website. Wenn keine Informationen gefunden werden, wird eine entsprechende Nachricht zurückgegeben oder ein Fehlerstring.
    '''
    if not re.match(r'^https://www\.([a-zA-Z0-9-]+\.)?uni-augsburg\.de(/.*)?$', url):
        return 'Fehler: Ungültige URL. Bitte gib eine URL von der Universität Augsburg an. Diese muss mit "https://www.uni-augsburg.de" beginnen.'

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; MyAgent/1.0)"
            })
            response.raise_for_status()
    except httpx.HTTPError as e:
        return f"Failed to fetch {url}: {e}"

    text = trafilatura.extract(response.text, include_links=True)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replacer, text) # type: ignore
    if not text:
        return f"Es konnte kein Text von {url} extrahiert werden."

    return text



@tool
async def suche_uni_augsburg(query: str, k: int = 3) -> list[str]:
    '''
    Findet Seiten der Uni Augsburg mit Informationen zu dem Query.

    Args:
        query (str): Die Suchanfrage, die Informationen zu einem Studiengang oder studiengangsbezogenen Fragen enthält. Mache deutlich, dass sich das Query auf die Universität Augsburg bezieht.
        k (int): Die Anzahl der zurückzugebenden relevanten Ergebnisse. Empfohlen sind 2 oder 3, da die Rückgabe sonst sehr lang werden kann.
    Returns:
        list[str]: Die relevantesten Informationen von der Website der Universität Augsburg, die der Anfrage entsprechen. Wenn keine relevanten Informationen gefunden werden, wird eine entsprechende Nachricht zurückgegeben.
    '''
    res = []
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
            res = await client.get(
                'http://localhost:8888/search?q=',
                params={'q': f'site:uni-augsburg.de {query}', 'format': 'json'},
                headers={
                    "Accept": "application/json",
                }
            )
            res.raise_for_status()
    except httpx.HTTPError:
        return ["Fehler bei der Suche"]
    # TODO: load additional pages when results smaller than k
    res = [{k: v for k, v in i.items() if k in ['title', 'content', 'url']} for i in res.json().get('results', [])][:k]
    res = [r['url'] for r in res if re.match(r'^https://www\.([a-zA-Z0-9-]+\.)?uni-augsburg\.de(/.*)?$', r['url'])]
    if not res:
        return ['Keine passenden Informationen gefunden.']
    results = []
    for url in res:
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; MyAgent/1.0)"
                })
                response.raise_for_status()
        except httpx.HTTPError:
            continue

        text = trafilatura.extract(response.text, include_links=True)
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replacer, text) # type: ignore
        if not text:
            continue
        results.append(f'Quelle: {url}\n{text}')
    if not results:
        return ['Keine passenden Informationen gefunden.']
    return results


################################################################
'''
Create workflow
'''
################################################################

class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int


# Augment the LLM with tools
tools = [search_studiengang, suche_uni_augsburg]
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
        Du kannst Informationen aus folgenden Bereichen zur Suche verwenden und diese sind immer in der Antwort enthalten:
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
    - suche_uni_augsburg: Findet Seiten der Uni Augsburg mit Informationen zu dem Query. Mache deutlich, dass sich das Query auf die Universität Augsburg bezieht.
'''
'''
    - suche_uni_augsburg_website: Durchsucht die Website der Universität Augsburg nach Informationen zu Studiengängen, Modulen und Klausuren.
        Du musst eine URL von der Universität Augsburg angeben, die mit "https://www.uni-augsburg.de" beginnt.
        Auf der Website können weitere Links der Universtät Augsburg verlinkt sein, die Du in einem neuen Tool-Aufruf durchsuchen kannst. Du darfst nur die Website der Universität Augsburg durchsuchen, keine anderen Websites.
        Suche IMMER zuerst auf https://www.uni-augsburg.de nach Links zu deinem Thema und suche dann diese Links.
        Verwende NUR URLS, die in einem vorherigen Tool-Aufruf von suche_uni_augsburg_website zurückgegeben wurden. Du darfst keine anderen URLs verwenden.
        Gebe nicht zu früh auf, sondern suche nach URLs in der Response des Tools, die zu deinem Thema passen. Suche dann diese URLs in einem neuen Tool-Aufruf. Viele wichtige URLs sind bereits auf der Startseite vorhanden.
        Gebe immer die verwendete Quelle mit an.
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

@cl.on_message
async def main(message: cl.Message):
    msg = cl.Message(content="")
    await msg.send()
    last_run_id = None

    run = await agent.astream_events(
        {"messages": [HumanMessage(content=message.content)]},
        version="v3"
    )
    async for event in run:
        res = get_info(event)

        if res['type'] == 'tool_call':
            tool_name = event['params']['data'][0]['content']['name']
            args = event['params']['data'][0]['content']['args']
            arg_display = args.get('query', args)

            async with cl.Step(name=f"🛠️ {tool_name}", type="tool") as step:
                step.input = str(arg_display)
            last_run_id = None

        if res['type'] in ['text', 'text-delta'] \
                and event['params']['data'][1]['langgraph_path'][1] == 'llm_call' \
                and res['event'] != 'content-block-finish':
            current_run_id = event['params']['data'][1].get('run_id')

            if current_run_id != last_run_id and msg.content and not msg.content.endswith(('\n', ' ')):
                await msg.stream_token('\n\n')

            last_run_id = current_run_id
            if res['content']:
                await msg.stream_token(res['content'])
    await msg.update()
