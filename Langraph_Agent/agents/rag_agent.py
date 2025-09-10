# agents/rag_agent.py
from __future__ import annotations
import os, json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from langchain_community.chat_models import ChatOllama
from langchain_core.documents import Document
from langchain_core.messages import AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

# LLMs / embeddings
try:
    from langchain_groq import ChatGroq  # optional
except Exception:
    ChatGroq = None
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
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
    score_threshold: Optional[float] = None  # set (e.g., 0.3) to filter weak hits

    # models
    llm_provider: str = os.getenv("RAG_LLM_PROVIDER", "groq")  # "groq" | "openai"
    llm_name: str = os.getenv("RAG_LLM", "llama-3.1-8b-instant")
    embeddings: str = os.getenv("RAG_EMBEDDINGS", "hf:all-MiniLM-L6-v2")  # or "hf:all-MiniLM-L6-v2"

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
             "You are a precise shopping RAG agent. Answer the user using ONLY the context. "
             "Cite as [n] and include source/file in a bullet list named 'References'. "
             "If the context is insufficient, say you need more data."),
            ("human", "Query:\n{query}\n\nContext:\n{context}")
        ])
        self.chain = self.prompt | self.llm | StrOutputParser()

    # -- public ----------------------------------------------------------------
    async def aanswer(self, query: str) -> Dict[str, Any]:
        docs, ctx_text = await self._aretrieve(query)
        answer = await self.chain.ainvoke({"query": query, "context": ctx_text})
        return {"answer": answer, "citations": self._citations(docs), "documents": docs}

    def answer(self, query: str) -> Dict[str, Any]:
        docs, ctx_text = self._retrieve(query)
        answer = self.chain.invoke({"query": query, "context": ctx_text})
        return {"answer": answer, "citations": self._citations(docs), "documents": docs}

    # -- graph node ------------------------------------------------------------
    # Use this function directly in LangGraph
    async def node(self, state, runtime) -> Dict[str, List[AIMessage]]:
        # last user message wins
        msg = state["messages"][-1].content if state.get("messages") else state.get("query", "")
        result = await self.aanswer(msg)
        content = result["answer"]
        msg = AIMessage(content=content, additional_kwargs={"citations": result["citations"]})
        # You can also attach raw docs if your state schema has a field for it
        return {"messages": [msg], "citations": result["citations"]}

    # -- internals -------------------------------------------------------------
    def _retrieve(self, query: str) -> Tuple[List[Document], str]:
        docs = self.retriever.invoke(query)
        if self.cfg.score_threshold is not None and hasattr(self.vs, "similarity_search_with_score"):
            docs = [d for d, s in self.vs.similarity_search_with_score(query, k=self.cfg.top_k)
                    if s >= self.cfg.score_threshold]
        return docs, self._format_docs(docs)

    async def _aretrieve(self, query: str) -> Tuple[List[Document], str]:
        # retriever has no async API; call sync in a thread if desired
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
                "source": d.metadata.get("source") or d.metadata.get("file_path") or d.metadata.get("url"),
                "metadata": d.metadata
            })
        return out

    def _build_llm(self, provider: str, name: str):
        p = provider.lower()
        if p == "groq":
            return ChatGroq(api_key="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", model=name, temperature=0)
        if p == "openai" and os.getenv("OPENAI_API_KEY"):
            return ChatOpenAI(model=name, temperature=0)
        # fallback to local ollama
        return ChatOllama(model="llama3:8b", temperature=0)

    def _build_embeddings(self, spec: str):
        if spec.startswith("hf:"):
            model = spec.split("hf:", 1)[1] or "sentence-transformers/all-MiniLM-L6-v2"
            return HuggingFaceEmbeddings(model_name=model)
        # default: OpenAI
        return OpenAIEmbeddings(model=spec.split("openai:", 1)[1] if ":" in spec else spec)

    def _load_or_build_index(self) -> FAISS:
        # try load
        if os.path.isdir(self.cfg.index_dir):
            return FAISS.load_local(self.cfg.index_dir, self.embed_model, allow_dangerous_deserialization=True)

        # else build from corpus folder (PDF, .txt, .md supported via DirectoryLoader)
        os.makedirs(self.cfg.index_dir, exist_ok=True)
        os.makedirs(self.cfg.corpus_dir, exist_ok=True)

        loaders = [
            DirectoryLoader(self.cfg.corpus_dir, glob="**/*.txt", loader_cls=TextLoader, show_progress=True),
            DirectoryLoader(self.cfg.corpus_dir, glob="**/*.md", loader_cls=TextLoader, show_progress=True),
            DirectoryLoader(self.cfg.corpus_dir, glob="**/*.pdf", loader_cls=PyPDFLoader, show_progress=True),
        ]
        docs: List[Document] = []
        for ld in loaders:
            try:
                docs.extend(ld.load())
            except Exception:
                pass

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        chunks = splitter.split_documents(docs) if docs else []
        vs = FAISS.from_documents(chunks, self.embed_model) if chunks else FAISS.from_texts(["empty"], self.embed_model)
        vs.save_local(self.cfg.index_dir)
        return vs


# -------- convenience factory + tool binding (optional) -----------------------

def get_rag_agent(cfg: Optional[RAGConfig] = None) -> RAGAgent:
    return RAGAgent(cfg or RAGConfig())

# Optional: expose a tool if you prefer tool-calling rather than a node
try:
    from langchain_core.tools import tool
    @tool("rag_search", return_direct=False)
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

    rag = get_rag_agent(cfg)

    q = "What is the return window and how do I contact support?"
    res = rag.answer(q)

    print("=== ANSWER ===")
    print(res["answer"])

