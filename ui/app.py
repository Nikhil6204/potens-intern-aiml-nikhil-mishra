"""
Streamlit UI for the RAG system.

Run with:
    streamlit run ui/app.py

Assumes the FastAPI backend is running at BACKEND_URL (default localhost:8000).
"""
import os
import sys

import requests
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Document Q&A with Citations", page_icon="📄", layout="wide")

st.title("📄 Document Q&A with Citations")
st.caption(
    "RAG over 5 AI-governance policy documents · multilingual · cites sources · "
    "refuses to answer what isn't in the docs"
)


def backend_get(path, **kwargs):
    return requests.get(f"{BACKEND_URL}{path}", timeout=60, **kwargs)


def backend_post(path, json_body):
    return requests.post(f"{BACKEND_URL}{path}", json=json_body, timeout=60)


# ---- Sidebar: document list & backend health ----
with st.sidebar:
    st.header("📚 Ingested Documents")
    try:
        docs_resp = backend_get("/documents")
        if docs_resp.status_code == 200:
            docs = docs_resp.json()
            for d in docs:
                st.markdown(f"**{d['title']}**  \n`{d['doc_id']}` · {d['num_chunks']} chunks")
        else:
            st.error("Could not load documents. Did you run `python -m ingest.ingest`?")
            docs = []
    except requests.exceptions.ConnectionError:
        st.error(f"Backend not reachable at {BACKEND_URL}. Start it with:\n\n"
                  f"`uvicorn backend.main:app --reload --port 8000`")
        docs = []

    st.divider()
    st.header("⚙️ Settings")
    top_k = st.slider("Retrieval top-k", min_value=1, max_value=10, value=5)
    use_reranker = st.checkbox("Use cross-encoder reranker (stretch feature)", value=False)

tab_ask, tab_contradict, tab_eval = st.tabs(["🔎 Ask", "⚖️ Contradiction Check", "📊 Eval"])

# ---------------- ASK TAB ----------------
with tab_ask:
    st.subheader("Ask a question in any language")
    example_cols = st.columns(3)
    example_qs = [
        "How many days does a vendor have to delete data after contract termination?",
        "¿Cuál es la ventana de escalamiento para incidentes SEV-1?",
        "मॉडल जोखिम समिति को गंभीर घटनाओं की सूचना कितने घंटों में देनी होगी?",
    ]
    if "question_input" not in st.session_state:
        st.session_state.question_input = ""
    for col, q in zip(example_cols, example_qs):
        if col.button(q, use_container_width=True):
            st.session_state.question_input = q

    question = st.text_area("Your question", value=st.session_state.question_input, height=80)

    if st.button("Ask", type="primary"):
        if not question.strip():
            st.warning("Type a question first.")
        else:
            with st.spinner("Retrieving and generating..."):
                try:
                    resp = backend_post("/ask", {"question": question, "top_k": top_k, "use_reranker": use_reranker})
                except requests.exceptions.ConnectionError:
                    st.error("Backend not reachable.")
                    resp = None

            if resp is not None:
                if resp.status_code != 200:
                    st.error(f"Error: {resp.text}")
                else:
                    data = resp.json()
                    lang = data.get("language", {})
                    st.caption(f"Detected question language: **{lang.get('name', 'unknown')}**")

                    if data.get("error"):
                        st.error(f"LLM call failed: {data['error']}")
                    elif data.get("covered") is False:
                        st.warning(f"🚫 **Not covered by the documents:** {data['answer']}")
                        if data.get("note"):
                            st.caption(data["note"])
                    else:
                        if data.get("needs_human_review"):
                            st.warning("⚠️ Low confidence — flagged for human review.")
                        st.markdown(f"### Answer\n{data['answer']}")
                        st.progress(min(max(data["confidence"], 0.0), 1.0),
                                    text=f"Confidence: {data['confidence']:.2f}")

                        if data.get("citations"):
                            st.markdown("### Citations")
                            for c in data["citations"]:
                                with st.expander(f"📎 {c['source']} — {c['section']} ({c['chunk_id']})"):
                                    st.write(c["snippet"])
                        else:
                            st.info("No citations returned.")

# ---------------- CONTRADICTION TAB ----------------
with tab_contradict:
    st.subheader("Check two documents for contradictions")
    if docs:
        doc_options = {f"{d['title']} ({d['doc_id']})": d["doc_id"] for d in docs}
        col1, col2 = st.columns(2)
        with col1:
            label_a = st.selectbox("Document A", list(doc_options.keys()), index=1 if len(doc_options) > 1 else 0)
        with col2:
            default_b_idx = 4 if len(doc_options) > 4 else min(2, len(doc_options) - 1)
            label_b = st.selectbox("Document B", list(doc_options.keys()), index=default_b_idx)

        if st.button("Check for contradictions", type="primary"):
            doc_id_a, doc_id_b = doc_options[label_a], doc_options[label_b]
            if doc_id_a == doc_id_b:
                st.warning("Pick two different documents.")
            else:
                with st.spinner("Aligning sections and analyzing..."):
                    try:
                        resp = backend_post("/contradict", {"doc_id_a": doc_id_a, "doc_id_b": doc_id_b})
                    except requests.exceptions.ConnectionError:
                        st.error("Backend not reachable.")
                        resp = None

                if resp is not None:
                    if resp.status_code != 200:
                        st.error(f"Error: {resp.text}")
                    else:
                        data = resp.json()
                        if data["contradicts"]:
                            st.error(f"⚠️ **Contradiction found**\n\n{data['summary']}")
                        else:
                            st.success(f"✅ **No contradiction found**\n\n{data['summary']}")

                        st.markdown("### Evidence (topically-aligned section pairs)")
                        for ev in data["evidence"]:
                            icon = "🔴" if ev["conflicts"] else "⚪"
                            with st.expander(
                                f"{icon} {ev['topic']} (alignment similarity: {ev['alignment_similarity']:.2f})"
                            ):
                                st.write(f"**Reasoning:** {ev['reasoning']}")
                                c1, c2 = st.columns(2)
                                with c1:
                                    st.markdown(f"**{ev['doc_a_snippet']['source']}** — "
                                                f"{ev['doc_a_snippet']['section']}")
                                    st.caption(ev["doc_a_snippet"]["text"])
                                with c2:
                                    st.markdown(f"**{ev['doc_b_snippet']['source']}** — "
                                                f"{ev['doc_b_snippet']['section']}")
                                    st.caption(ev["doc_b_snippet"]["text"])
    else:
        st.info("No documents loaded.")

# ---------------- EVAL TAB ----------------
with tab_eval:
    st.subheader("Retrieval eval (10 Q&A pairs with ground truth)")
    st.caption("Scores retrieval@k: did the correct document appear in the top-k retrieved chunks? "
               "Also checks that the one intentionally out-of-scope question is correctly refused.")
    if st.button("Run eval"):
        with st.spinner("Running eval set..."):
            try:
                resp = backend_get("/eval")
            except requests.exceptions.ConnectionError:
                st.error("Backend not reachable.")
                resp = None
        if resp is not None:
            if resp.status_code != 200:
                st.error(f"Error: {resp.text}")
            else:
                data = resp.json()
                c1, c2 = st.columns(2)
                c1.metric(f"Retrieval@{data['k']}", f"{data['retrieval_at_k']*100:.0f}%",
                           f"{data['retrieval_hits']}/{data['retrieval_scored_questions']}")
                c2.metric("Out-of-scope question correctly refused",
                          "✅ Yes" if data["out_of_scope_refusal_correct"] else "❌ No")

                st.markdown("### Per-question detail")
                for d in data["details"]:
                    if d.get("is_out_of_scope_trap"):
                        st.write(f"**{d['id']}** (trap question): *{d['question']}*")
                        st.caption(f"System answer: {d['system_answer']}")
                    else:
                        icon = "✅" if d["hit_at_k"] else "❌"
                        st.write(f"{icon} **{d['id']}**: {d['question']}")
                        st.caption(f"expected: {d['expected_doc_id']} · retrieved: {d['retrieved_doc_ids']}")
