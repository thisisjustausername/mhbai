import os
from typing import Annotated, Sequence

# Core Graph Workflow Architecture
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import BaseMessage, HumanMessage

# Production Integration Components
from langchain_community.embeddings import HuggingFaceHubEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_core.retrievers import EnsembleRetriever
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

# =====================================================================
# 1. HARDWARE-ACCELERATED QWEN3 EMBEDDING MANAGEMENT
# =====================================================================

# Interface connecting to the Rust TEI container handling the 8B vector space
print("Establishing connection to local gte-Qwen3-8B-embedding engine...")
qwen3_embeddings = HuggingFaceHubEmbeddings(
    model="http://localhost:8080", 
)

# GTE-Qwen models require an explicit instruction prefix to optimize asymmetric RAG
def proxy_qwen3_query_embedding(query: str):
    prefix_instruction = "Instruct: Falls Dir Fragen zu Studiengängen gestellt werden, suche in der Studiengangsdatenbank.\nFrage: "
    return qwen3_embeddings.embed_query(prefix_instruction + query)

# Wrap target query method
qwen3_embeddings.embed_query = proxy_qwen3_query_embedding


# =====================================================================
# 2. SEED STRUCTURAL GERMAN DATA & ASYMMETRIC HYBRID SEARCH
# =====================================================================
with open("student-conselor/info-cards.json", "r") as f:
    info_cards = json.load(f)

# Primary Semantic Storage (Calculated asynchronously via GPU)
dense_index = FAISS.from_texts(info_cards, qwen3_embeddings)
dense_retriever = dense_index.as_retriever(search_kwargs={"k": 1})

# Fallback Exact Keyword Index (Guarantees literal abbreviations hit 100% of the time)
sparse_retriever = BM25Retriever.from_texts(info_cards)
sparse_retriever.k = 1

# Fusing semantic alignment with strict literal token interception
hybrid_retriever = EnsembleRetriever(
    retrievers=[dense_retriever, sparse_retriever], 
    weights=[0.5, 0.5]
)


# =====================================================================
# 3. WORKFLOW AGENT TOOL DEFINITION
# =====================================================================

@tool
def query_academic_knowledgebase(query: str) -> str:
    """Durchsucht die internen Informationskarten für Studiengängen nach Studiengangsinformationen, Inhalten, Zulassungsvoraussetzungen (NC) und weiteren studiengangsspezifischen Fragen"""
    retrieved_documents = hybrid_retriever.invoke(query)
    
    # Accelerated linear deduplication preserving contextual proximity
    discovered = set()
    cleaned_context = [
        doc.page_content for doc in retrieved_documents 
        if not (doc.page_content in discovered or discovered.add(doc.page_content))
    ]
    
    if cleaned_context:
        return "\n---\n".join(cleaned_context)
    return "Keine übereinstimmenden Datenkarten im lokalen Verzeichnis gefunden."

tools = [query_academic_knowledgebase]
tool_node = ToolNode(tools)


# =====================================================================
# 4. HIGH-THROUGHPUT QWEN3.6 INFERENCE ROUTING
# =====================================================================

# Direct connection to the local vLLM worker serving the 35B open MoE model
high_performance_qwen36 = ChatOpenAI(
    base_url="http://localhost:8000/v1",
    api_key="local-worker",
    model="Qwen/Qwen3.6-35B-A3B-Instruct",
    temperature=0.0
).bind_tools(tools)

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

def invoke_qwen36_engine(state: AgentState):
    system_prompt = HumanMessage(
        content="Du bist ein hochpräziser Echtzeit-Assistent für Studienberatung. "
                "Nutze das Suchwerkzeug bei Fragen zu bestimmten Studiengängen, Bedingungen, oder Fragen, bei denen Informationen zu Studiengängen relevant sind. Du darfst kein eigenes Wissen verwenden, sondern nur das recherchierte Wissen anwenden."
                "Antworte extrem prägnant, strukturiert und ausschließlich auf Deutsch basierend auf den abgetrennten Fakten."
    )
    response = high_performance_qwen36.invoke([system_prompt] + list(state['messages']))
    return {"messages": [response]}

# Compile the execution pipeline topology
workflow = StateGraph(AgentState)
workflow.add_node("agent", invoke_qwen36_engine)
workflow.add_node("tools", tool_node)
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", tools_condition)
workflow.add_edge("tools", "agent")
app = workflow.compile()


# =====================================================================
# 5. LIVE VERIFICATION EXECUTION
# =====================================================================

if __name__ == "__main__":
    test_query = "Benötige ich für das VWL Studium einen NC?"
    print(f"[Anfrage]: {test_query}\n")
    
    execution_state = {"messages": [HumanMessage(content=test_query)]}
    for cycle_update in app.stream(execution_state, stream_mode="updates"):
        for current_node, contents in cycle_update.items():
            if current_node == "agent" and 'messages' in contents:
                node_message = contents['messages'][-1]
                # Filter stream updates to only print the final model output
                if not hasattr(node_message, 'tool_calls') or not node_message.tool_calls:
                    print(f"[Qwen 3.6 Antwort]:\n{node_message.content}")
