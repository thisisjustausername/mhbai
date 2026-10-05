'''
Demonstrates a StateGraph workflow that augments a ChatOllama model with a
search tool backed by a Chroma vector store. This example is async and uses
streaming to print incremental model output.

Run using: chainlit run student_counselor/langgraph/graph.py --host 127.0.0.1 --port 8000
'''

# TODO: for module_handbook, module and exam mongodb search make embedding input dict and convert it to infocard

import operator
import warnings
from typing import Annotated, Literal

import chainlit as cl
from langchain.messages import AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core._api.beta_decorator import LangChainBetaWarning
from langchain_ollama import ChatOllama
from langgraph.graph import END, START, StateGraph
from mhbai.student_counselor.langgraph.tools import (
    dirty_search,
    get_klausur,
    get_klausur_by_mongodb_id,
    get_modul,
    get_modul_by_mongodb_id,
    get_modulhandbuch_by_mongodb_id,
    get_studiengang_modulhandbuch,
    mdl,
    search_studiengang,
)
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from typing_extensions import TypedDict

warnings.filterwarnings('ignore', category=LangChainBetaWarning)


model = ChatOllama(
    model=mdl,
    temperature=0.5,
    num_predict=4096,
    num_ctx=262144,
    streaming=True
)

################################################################
'''
Create workflow
'''
################################################################

class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int


# Augment the LLM with tools
tools = [search_studiengang, dirty_search, get_studiengang_modulhandbuch, get_modul, get_klausur, get_klausur_by_mongodb_id, get_modul_by_mongodb_id, get_modulhandbuch_by_mongodb_id]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)

# TODO: put tool descriptions in another tool called tool info tool that provides information about the tools and their usage, so that only their use case has to be put in the prompt
# TODO: make infocard tool for searching for workloads, etc. in get_modul
system_prompt = '''Du bist ein hochpräziser Assistent für die Studienberatung.
Nutze das Suchwerkzeug bei Fragen zu bestimmten Studiengängen, Bedingungen, oder Fragen, bei denen Informationen zu Studiengängen relevant sind. Du darfst kein eigenes Wissen verwenden, sondern nur das recherchierte Wissen anwenden.
Antworte auf Deutsch und in schönem Markdown-Format.
Auf Fragen, die nichts mit dem Studium zu tun haben, oder eine Meinung fordern, antworte mit 'Darüber habe ich leider keine Kenntnisse.'

Regeln:
    - Verwende das Suchwerkzeug, um Informationen zu Studiengängen zu finden
    - Wenn das Suchwerkzeug keine Ergebnisse liefert, verwende das Tool dirty_search, um Informationen
    - Antworte auf Deutsch und in schönem Markdown-Format
    - Führe die Tools nur NACHEINANDER aus, nicht gleichzeitig. Warte auf die Antwort des Tools, bevor du das nächste Tool aufrufst.
    - Entnehme dabei das Wissen aus der ANTWORT DES SEARCH-TOOLS
    - Gebe immer eine Antwort. Wenn du keine Informationen findest, teile dies in deiner Antwort mit.
    - Duze die Nutzer/in
    - Gebe nur Links der Universität Augsburg aus.

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
    - dirty_search: Durchsucht die offiziellen Websiten der Universität Augsburg auf passende Ergebnisse. (Search-Tool)
            * Verwende dirty_search als Fallback, wenn search_intranet nichts findet.
            * dirty_search findet nur öffentlich zugängliche Websites der Universität Augsburg und ist geeignet für Queries, die Typos enthalten.
            * Mache deutlich, dass sich das Query auf die Universität Augsburg bezieht.
    Verwende die folgenden Tools, um nach Klausuren, Modulen oder Studiengängen zu suchen, wenn du deren MongoDB-ID nicht kennst.
    - get_klausur: Gibt Informationen zu passenden Klausuren zurück.
        Du kannst Informationen aus folgenden Bereichen zur Suche verwenden und diese sind immer in der Antwort enthalten:
            * name: Name der Klausur
            * description: Beschreibung der Klausur
            * preparation: Vorbereitung auf die Klausur
            * type: Typ der Klausur z.B. mündlich, schriftlich, Hausarbeit, Seminararbeit, ...
            * duration: Dauer der Klausur
            * frequency: Häufigkeit der Klausur, z.B. einmal pro Semester, einmal pro Jahr, ...
            * deadline: Deadline der Klausur
            * graded: Ob die Klausur benotet ist
            * id: ID der Klausur, diese muss nicht eindeutig sein
            * portion_of_grade: Anteil an der Note der Klausur in dem verwendeten Modul
        Du musst immer mindestens einen semantischen Parameter (name, description, preparation, type, duration, frequency) angeben, um die Suche zu starten. Die anderen Parameter sind optional und können als Filter verwendet werden.
    - get_modul: Gibt Informationen zu passenden Modulen zurück.
        Du kannst Informationen aus folgenden Bereichen zur Suche verwenden und diese sind immer in der Antwort enthalten:
            * name: Name des Moduls
            * content: Inhalt des Moduls
            * goals: Ziele des Moduls
            * lecturer: Dozent des Moduls
            * prerequisites: Voraussetzungen des Moduls
            * faculty_chair: Lehrstuhl des Moduls
            * workloads: Arbeitsbelastung des Moduls
            * success_requirements: Erfolgsvoraussetzungen des Moduls
            * exam_outline: Prüfungsordnung des Moduls
            * mandatory: Ob das Modul verpflichtend ist
            * module_code: Modulcode des Moduls
            * ects: ECTS-Punkte des Moduls
            * available_semesters: Verfügbare Semester des Moduls
            * recommended_semester_span: Empfohlene Semesteranzahl des Moduls
            * languages: Sprachen des Moduls
            * international: Ob das Modul international ist
            * weekly_hours: Wöchentliche Stunden des Moduls
            * workload_hours: Arbeitsstunden des Moduls
            * exams: Prüfungen des Moduls
        Verwende immer mindestens einen semantischen Parameter (name, content, goals, lecturer, prerequisites, faculty_chair, workloads, success_requirements, exam_outline), um die Suche zu starten. Die anderen Parameter sind optional und können als Filter verwendet werden.
    - get_studiengang_modulhandbuch: Gibt das Modulhandbuch für einen bestimmten Studiengang zurück.
        Du kannst Informationen aus folgenden Bereichen zur Suche verwenden und diese sind immer in der Antwort enthalten:
            * name: Name des Modulhandbuchs
            * description: Ab wann man den Studiengang studieren kann
            * faculties: Fakultäten des Studiengangs
            * path: Pfad des Modulhandbuchs
            * start_semester: Startsemester des Modulhandbuchs
        Verwende immer mindestens einen semantischen Parameter (name, description, faculties, path), um die Suche zu starten. Der Parameter start_semester ist optional und kann als Filter verwendet werden.
    Verwende die folgenden Tools, um nach Klausuren, Modulen oder Studiengängen zu suchen, wenn du deren MongoDB-ID kennst (die MongoDB-IDs findest du durch die Tools get_klausur, get_modul oder get_studiengang_modulhandbuch)
    - get_modulhandbuch_by_mongodb_id: Gibt ausführliche Informationen zu einem Modulhandbuch anhand der MongoDB-ID zurück.
    - get_modul_by_mongodb_id: Gibt Informationen zu einem Modul anhand der MongoDB-ID zurück.
    - get_klausur_by_mongodb_id: Gibt Informationen zu einer Klausur anhand der MongoDB-ID zurück.
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
    msg = cl.Message(content='')
    await msg.send()
    last_run_id = None

    run = await agent.astream_events(
        {'messages': [HumanMessage(content=message.content)]},
        version='v3'
    )
    async for event in run:
        res = get_info(event)

        if res['type'] == 'tool_call':
            tool_name = event['params']['data'][0]['content']['name']
            args = event['params']['data'][0]['content']['args']
            arg_display = args.get('query', args)

            async with cl.Step(name=f'🛠️ {tool_name}', type='tool') as step:
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
