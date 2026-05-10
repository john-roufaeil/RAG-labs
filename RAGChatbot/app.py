import streamlit as st
import rag_engine

st.set_page_config(page_title="RAG Chatbot", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []

BADGE_COLOUR = {
    "rag":       "#2563eb",
    "off_topic": "#9333ea",
    "no_docs":   "#dc2626",
}

def badge(label: str, source: str) -> str:
    colour = BADGE_COLOUR.get(source, "#6b7280")
    return (
        f'<span style="background:{colour};color:white;padding:2px 8px;'
        f'border-radius:9999px;font-size:0.72rem;font-weight:600;">{label}</span>'
    )

with st.sidebar:
    st.title("RAG Chatbot")
    if rag_engine.db:
        count = rag_engine.db._collection.count()
        st.success(f"**{count} chunks** indexed")
    else:
        st.warning("No documents indexed yet.")
    uploaded = st.file_uploader(
        "Drop PDF files here", type="pdf", accept_multiple_files=True
    )
    if st.button("Index Documents", disabled=not uploaded, use_container_width=True):
        with st.spinner("Reading and indexing…"):
            n = rag_engine.index_documents(uploaded)
        st.success(f"Indexed {n} chunks!")
        st.rerun()
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

st.title("Chat")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant" and "badge_html" in msg:
            st.markdown(msg["badge_html"], unsafe_allow_html=True)
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask a question…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            result = rag_engine.query(prompt, st.session_state.messages)
        badge_html = badge(result["badge"], result["source"])
        st.markdown(badge_html, unsafe_allow_html=True)
        st.markdown(result["answer"])
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["answer"],
            "badge_html": badge_html,
        }
    )