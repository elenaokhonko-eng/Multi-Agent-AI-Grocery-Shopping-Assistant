# agents/rag_agent.py
from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from langsmith import traceable

from langchain_core.documents import Document
from langchain_core.messages import AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

# LLMs / embeddings
try:
    from langchain_ollama import ChatOllama  # optional if you use Groq
except Exception: ChatOllama = None

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import HuggingFaceEmbeddings

# Vector store + loaders
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader


# ---- Config -----------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent                 # .../Langraph_Agent/agents
DEFAULT_CORPUS = BASE_DIR / "data" / "rag_corpus"
DEFAULT_INDEX  = BASE_DIR.parent / "vectorstore" / "faiss_index"  # .../Langraph_Agent/vectorstore/faiss_index

@dataclass
class RAGConfig:
    # paths
    index_dir: str = os.getenv("RAG_INDEX_DIR", str(DEFAULT_INDEX))
    corpus_dir: str = os.getenv("RAG_CORPUS_DIR", str(DEFAULT_CORPUS))
    top_k: int = 6
    score_threshold: Optional[float] = None  # e.g. 0.3 to filter weaker hits

    # models
    llm_provider: str = os.getenv("RAG_LLM_PROVIDER", "groq")  # groq | openai | ollama
    llm_name: str = os.getenv("RAG_LLM", "llama-3.1-8b-instant")
    embeddings: str = os.getenv("RAG_EMBEDDINGS", "hf:all-MiniLM-L6-v2")  # or openai:text-embedding-3-small


# ---- RAG Agent ---------------------------------------------------------------
class RAGAgent:
    def __init__(self, cfg: RAGConfig):
        self.cfg = cfg
        self.embed_model = self._build_embeddings(cfg.embeddings)
        self.vs = self._load_or_build_index()
        self.retriever = self.vs.as_retriever(search_kwargs={"k": cfg.top_k})

        self.llm = self._build_llm(cfg.llm_provider, cfg.llm_name)

        self.prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are a precise shopping RAG agent. Answer using ONLY the context.\n"
             "Cite as [n] and include a bullet list named 'References' with file/source.\n"
             "If the context is insufficient, say you need more data."),
            ("human", "Query:\n{query}\n\nContext:\n{context}")
        ])

        # Add default tags/metadata so all RAG calls show up in LangSmith clearly
        self.chain = (self.prompt | self.llm | StrOutputParser()).with_config({
            "tags": ["titanstore", "rag", "agent"],
            "metadata": {"component": "rag_agent"}
        })

    # -- public ----------------------------------------------------------------
    @traceable(name="rag_answer_sync", tags=["titanstore", "rag"])
    def answer(self, query: str) -> Dict[str, Any]:
        docs, ctx_text = self._retrieve(query)
        answer = self.chain.invoke(
            {"query": query, "context": ctx_text},
            config={"tags": ["rag", "answer"], "metadata": {"query": query}}
        )
        return {"answer": answer, "citations": self._citations(docs), "documents": docs}

    @traceable(name="rag_answer_async", tags=["titanstore", "rag"])
    async def aanswer(self, query: str) -> Dict[str, Any]:
        docs, ctx_text = await self._aretrieve(query)
        answer = await self.chain.ainvoke(
            {"query": query, "context": ctx_text},
            config={"tags": ["rag", "answer"], "metadata": {"query": query}}
        )
        return {"answer": answer, "citations": self._citations(docs), "documents": docs}

    # -- graph node ------------------------------------------------------------
    # Use this function directly in LangGraph
    @traceable(name="rag_node", tags=["titanstore", "langgraph", "node"])
    async def node(self, state, runtime) -> Dict[str, List[AIMessage]]:
        # last user message wins
        msg = state["messages"][-1].content if state.get("messages") else state.get("query", "")
        result = await self.aanswer(msg)
        content = result["answer"]
        msg = AIMessage(content=content, additional_kwargs={"citations": result["citations"]})
        return {"messages": [msg], "citations": result["citations"]}

    # -- internals -------------------------------------------------------------
    @traceable(name="rag_retrieve_sync", tags=["titanstore", "rag", "retrieval"])
    def _retrieve(self, query: str) -> Tuple[List[Document], str]:
        docs = self.retriever.invoke(query)
        # Optional score filtering if FAISS similarity scores are exposed
        if self.cfg.score_threshold is not None and hasattr(self.vs, "similarity_search_with_score"):
            pairs = self.vs.similarity_search_with_score(query, k=self.cfg.top_k)
            # For FAISS in LangChain, higher score is generally better; filter accordingly.
            docs = [d for d, s in pairs if s >= self.cfg.score_threshold]
        return docs, self._format_docs(docs)

    async def _aretrieve(self, query: str) -> Tuple[List[Document], str]:
        # retriever has no async API; call sync for simplicity
        return self._retrieve(query)

    @staticmethod
    def _format_docs(docs: List[Document]) -> str:
        lines = []
        for i, d in enumerate(docs, 1):
            src = d.metadata.get("source") or d.metadata.get("file_path") or d.metadata.get("url") or "unknown"
            lines.append(f"[{i}] {d.page_content}\nSOURCE={src}")
        return "\n\n".join(lines)

    @staticmethod
    def _citations(docs: List[Document]) -> List[Dict[str, Any]]:
        out = []
        for i, d in enumerate(docs, 1):
            out.append({
                "id": i,
                "source": d.metadata.get("source") or d.metadata.get("file_path") or d.metadata.get("url") or "unknown",
                "metadata": d.metadata,
            })
        return out

    @traceable(name="rag_build_llm", tags=["titanstore", "rag"])
    def _build_llm(self, provider: str, name: str):
        p = (provider or "").lower()
        if p == "groq" and ChatGroq:
            # Read from env; do not hardcode secrets
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise RuntimeError("GROQ_API_KEY not set")
            return ChatOllama(base_url=Config.OLLAMA_BASE_URL, model=name, temperature=0)
        if p == "openai":
            # Requires OPENAI_API_KEY in environment
            return ChatOpenAI(model=name, temperature=0)
        # fallback to local ollama
        return ChatOllama(model="llama3:8b", temperature=0)

    @traceable(name="rag_build_embeddings", tags=["titanstore", "rag"])
    def _build_embeddings(self, spec: str):
        if spec.startswith("hf:"):
            model = spec.split("hf:", 1)[1] or "sentence-transformers/all-MiniLM-L6-v2"
            return HuggingFaceEmbeddings(model=model)
        # default to OpenAI embeddings if prefixed with openai:*
        if spec.startswith("openai:"):
            model = spec.split("openai:", 1)[1] or "text-embedding-3-small"
            return OpenAIEmbeddings(model=model)
        # if spec is a bare non-hf string, assume OpenAI model name
        if ":" not in spec:
            return OpenAIEmbeddings(model=spec)
        # final fallback
        return HuggingFaceEmbeddings(model="sentence-transformers/all-MiniLM-L6-v2")

    @traceable(name="rag_load_or_build_index", tags=["titanstore", "rag", "index"])
    def _load_or_build_index(self) -> FAISS:
        index_dir = Path(self.cfg.index_dir)
        corpus_dir = Path(self.cfg.corpus_dir)

        # Try loading
        if index_dir.is_dir():
            return FAISS.load_local(str(index_dir), self.embed_model, allow_dangerous_deserialization=True)

        # Else build from corpus folder (PDF, .txt, .md supported)
        index_dir.mkdir(parents=True, exist_ok=True)
        corpus_dir.mkdir(parents=True, exist_ok=True)

        loaders = [
            DirectoryLoader(str(corpus_dir), glob="**/*.txt", loader_cls=TextLoader, show_progress=True),
            DirectoryLoader(str(corpus_dir), glob="**/*.md", loader_cls=TextLoader, show_progress=True),
            DirectoryLoader(str(corpus_dir), glob="**/*.pdf", loader_cls=PyPDFLoader, show_progress=True),
        ]
        docs: List[Document] = []
        for ld in loaders:
            try:
                docs.extend(ld.load())
            except Exception:
                # ignore loader errors but continue
                pass

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        chunks = splitter.split_documents(docs) if docs else []

        vs = FAISS.from_documents(chunks, self.embed_model) if chunks else FAISS.from_texts(["empty"], self.embed_model)
        vs.save_local(str(index_dir))
        return vs


# -------- convenience factory + tool binding (optional) -----------------------
def get_rag_agent(cfg: Optional[RAGConfig] = None) -> RAGAgent:
    return RAGAgent(cfg or RAGConfig())

# Optional: expose a tool if you prefer tool-calling rather than a node
try:
    from langchain_core.tools import tool

    @tool("rag_search", return_direct=False)
    @traceable(name="rag_tool_search", tags=["titanstore", "rag", "tool"])
    def rag_search(query: str, top_k: int = 6) -> Dict[str, Any]:
        agent = get_rag_agent(RAGConfig(top_k=top_k))
        return agent.answer(query)
except Exception:
    pass


# -------- one-time CLI to build index ----------------------------------------
if __name__ == "__main__":
    cfg = RAGConfig()
    agent = RAGAgent(cfg)  # building happens inside if index doesn't exist
    print(f"FAISS index ready at: {cfg.index_dir}  | corpus: {cfg.corpus_dir}")

    q = "What is the return window and how do I contact support?"
    res = agent.answer(q)

    print("=== ANSWER ===")
    print(res["answer"])
    print("\n=== CITATIONS ===")
    for c in res["citations"]:
        print(f"[{c['id']}] {c['source']}")
