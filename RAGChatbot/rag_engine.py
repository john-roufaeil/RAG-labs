import os
import tempfile
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
from langchain.chat_models import init_chat_model

load_dotenv()

CHROMA_DIR = "./chroma_db"
COLLECTION = "my_collection"
NO_MATCH_THRESHOLD = 1.2

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
llm = init_chat_model("gpt-4o-mini", temperature=0)
db = None
topic = ""

def load_existing_db():
    global db, topic
    if os.path.exists(CHROMA_DIR):
        try:
            candidate = Chroma(
                collection_name=COLLECTION,
                embedding_function=embeddings,
                persist_directory=CHROMA_DIR,
            )
            if candidate._collection.count() > 0:
                db = candidate
                topic = infer_topic()
        except Exception:
            pass

def infer_topic(chunks=None) -> str:
    """Summarise what the loaded documents are about."""
    if chunks:
        sample = " ".join(c.page_content[:200] for c in chunks[:6])
    else:
        sample = " ".join(r.page_content[:200] for r in db.similarity_search("", k=6))

    res = llm.invoke(
        f"In one short sentence, what topic(s) do these document excerpts cover?\n\n{sample}"
    )
    return res.content.strip()

def index_documents(files) -> int:
    global db, topic

    raw_docs = []
    for file in files:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(file.read())
            tmp_path = tmp.name
        raw_docs.extend(PyPDFLoader(tmp_path).load())
        os.unlink(tmp_path)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=80,
        separators=["\n\n", "\n", " ", ""],
    )
    chunks = splitter.split_documents(raw_docs)

    db = Chroma.from_documents(
        chunks,
        embeddings,
        collection_name=COLLECTION,
        persist_directory=CHROMA_DIR,
    )
    topic = infer_topic(chunks)
    return len(chunks)


# --- Routing ---
def route_question(question: str) -> str:
    """Return 'rag' or 'off_topic'."""
    topic_line = f"The knowledge base covers: {topic}" if topic else "No documents loaded."
    prompt = f"""You are a query router for a document Q&A assistant.
{topic_line}

Classify the user question into exactly one category:
- "rag"       : Related to the document topics
- "off_topic" : Completely unrelated to the document topics

Question: {question}

Reply with exactly one word: rag or off_topic"""

    raw = llm.invoke(prompt).content.strip().lower()
    return "off_topic" if "off_topic" in raw else "rag"


# --- History formatting ---
def format_history(history: list[dict]) -> str:
    lines = []
    for msg in history[-6:]:
        role = "Human" if msg["role"] == "user" else "Assistant"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)


# --- Answering ---
def answer_from_docs(question: str, history: list[dict]) -> dict:
    results = db.similarity_search_with_score(question, k=3)

    if not results or results[0][1] > NO_MATCH_THRESHOLD:
        return {
            "answer": "I don't know. The answer doesn't appear to be in the uploaded documents.",
            "source": "rag",
            "badge": "Knowledge Base",
        }

    context = "\n\n".join(r[0].page_content for r in results)
    source_names = ", ".join(
        os.path.basename(r[0].metadata.get("source", "document"))
        for r in results
    )

    prompt = PromptTemplate(
        template="""Use the context below to answer the question accurately and concisely.
If the context does not contain the answer, say "I don't know."

Conversation history:
{history}

Context:
{context}

Question: {question}

Answer:""",
        input_variables=["history", "context", "question"],
    )

    res = llm.invoke(prompt.format(
        history=format_history(history),
        context=context,
        question=question,
    ))

    return {
        "answer": res.content,
        "source": "rag",
        "badge": f"Knowledge Base ({source_names})",
    }


# --- Main entry point ---
def query(question: str, history: list[dict]) -> dict:
    if db is None:
        return {
            "answer": "No documents loaded. Please upload PDFs using the sidebar.",
            "source": "no_docs",
            "badge": "No Documents",
        }

    if route_question(question) == "off_topic":
        return {
            "answer": f"I'm focused on: **{topic}**.\n\nThat's outside my scope — ask me something about the uploaded documents!",
            "source": "off_topic",
            "badge": "Off-Topic",
        }

    return answer_from_docs(question, history)


# Run once on import to pick up any existing DB
load_existing_db()