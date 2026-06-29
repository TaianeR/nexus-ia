import os
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

# ─────────────────────────────────────────────
# Configuração da Página
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Nexus IA – Seu Assistente Inteligente",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# CSS Premium – Identidade Nexus IA
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, .stApp {
        background: #080810;
        font-family: 'Inter', sans-serif;
        color: #e2e8f0;
    }

    #MainMenu, header, footer { visibility: hidden; }

    .block-container {
        padding-top: 0rem;
        padding-bottom: 5rem;
        max-width: 780px;
    }

    .nexus-hero {
        text-align: center;
        padding: 2.5rem 1rem 1.5rem 1rem;
    }

    .nexus-logo {
        width: 72px;
        height: 72px;
        border-radius: 20px;
        background: linear-gradient(135deg, #6366f1, #8b5cf6, #06b6d4);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        margin-bottom: 1rem;
        box-shadow: 0 0 40px rgba(139, 92, 246, 0.5), 0 0 80px rgba(99, 102, 241, 0.2);
        animation: pulse-glow 3s ease-in-out infinite;
    }

    @keyframes pulse-glow {
        0%, 100% { box-shadow: 0 0 40px rgba(139,92,246,0.5), 0 0 80px rgba(99,102,241,0.2); }
        50%       { box-shadow: 0 0 60px rgba(139,92,246,0.8), 0 0 120px rgba(99,102,241,0.4); }
    }

    .nexus-title {
        font-size: 2.4rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        background: linear-gradient(90deg, #a78bfa, #818cf8, #38bdf8, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        line-height: 1.1;
    }

    .nexus-subtitle {
        color: #64748b;
        font-size: 0.9rem;
        margin-top: 0.5rem;
        font-weight: 400;
        letter-spacing: 0.04em;
    }

    .message-row {
        display: flex;
        align-items: flex-end;
        gap: 10px;
        margin-bottom: 1rem;
        animation: slideIn 0.25s ease-out;
    }

    @keyframes slideIn {
        from { opacity: 0; transform: translateY(10px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    .message-row.user  { flex-direction: row-reverse; }
    .message-row.nexus { flex-direction: row; }

    .avatar {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        flex-shrink: 0;
    }

    .avatar-nexus {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        box-shadow: 0 0 12px rgba(139,92,246,0.5);
    }

    .avatar-user {
        background: linear-gradient(135deg, #0f172a, #1e293b);
        border: 1px solid #334155;
    }

    .bubble {
        padding: 13px 18px;
        border-radius: 18px;
        max-width: 82%;
        font-size: 0.925rem;
        line-height: 1.7;
    }

    .bubble-nexus {
        background: linear-gradient(135deg, #0f0f1e, #12122a);
        border: 1px solid #1e1e3f;
        border-bottom-left-radius: 4px;
        color: #e2e8f0;
    }

    .bubble-user {
        background: linear-gradient(135deg, #312e81, #3730a3);
        border: 1px solid #4338ca;
        border-bottom-right-radius: 4px;
        color: #eef2ff;
    }

    [data-testid="stChatInput"] textarea {
        background: #0f0f1e !important;
        border: 1px solid #1e1e3f !important;
        border-radius: 16px !important;
        color: #e2e8f0 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.93rem !important;
        padding: 14px 18px !important;
    }

    [data-testid="stChatInput"] textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99,102,241,0.2) !important;
    }

    .stSpinner > div { border-top-color: #8b5cf6 !important; }

    .suggestion-chip {
        display: inline-block;
        background: #0f0f1e;
        border: 1px solid #1e1e3f;
        border-radius: 20px;
        padding: 7px 15px;
        font-size: 0.82rem;
        color: #94a3b8;
        margin: 4px;
    }

    .stButton > button {
        background: transparent;
        border: 1px solid #1e1e3f;
        color: #64748b !important;
        border-radius: 10px;
        font-size: 0.82rem;
        padding: 6px 14px;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        border-color: #6366f1;
        color: #a78bfa !important;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Hero Header
# ─────────────────────────────────────────────
st.markdown("""
<div class="nexus-hero">
    <div class="nexus-logo">✦</div>
    <h1 class="nexus-title">Nexus IA</h1>
    <p class="nexus-subtitle">Inteligência Artificial · Sempre pronto para te ajudar</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Carregar API Key
# ─────────────────────────────────────────────
api_key = (
    st.secrets.get("GOOGLE_API_KEY", None)
    if hasattr(st, "secrets") else None
) or os.environ.get("GOOGLE_API_KEY", None)

if not api_key:
    st.markdown("""
    <div style='text-align:center; padding: 2rem; color:#64748b;'>
        ⚠️ Sistema em configuração. Tente novamente em breve.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

os.environ["GOOGLE_API_KEY"] = api_key

# ─────────────────────────────────────────────
# Modelo
# ─────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_llm():
    return ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7, max_output_tokens=2048)

llm = get_llm()

SYSTEM_PROMPT = """Você é o Nexus IA, um assistente de inteligência artificial avançado, inteligente e amigável.
Responda sempre em português do Brasil, de forma clara, natural e envolvente.
Você pode ajudar com qualquer assunto: perguntas gerais, criatividade, tecnologia, conselhos,
redação, análise, programação, dúvidas do dia a dia e muito mais.
Seja direto, útil e use uma linguagem acessível. Use emojis com moderação quando ficarem naturais."""

# ─────────────────────────────────────────────
# Histórico
# ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sugestões iniciais
if not st.session_state.messages:
    st.markdown("""
    <div style='text-align:center; padding: 1rem 0 0.5rem 0; color:#334155; font-size:0.85rem; letter-spacing:0.05em;'>
        EXPERIMENTE PERGUNTAR
    </div>
    <div style='text-align:center; margin-bottom: 1.5rem;'>
        <span class='suggestion-chip'>✍️ Escreva um texto para mim</span>
        <span class='suggestion-chip'>💡 Me dê uma ideia criativa</span>
        <span class='suggestion-chip'>🔧 Ajude com tecnologia</span>
        <span class='suggestion-chip'>📚 Explique um conceito</span>
        <span class='suggestion-chip'>🌍 Traduza algo</span>
        <span class='suggestion-chip'>🤔 Me aconselhe</span>
    </div>
    """, unsafe_allow_html=True)

# Renderizar histórico
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"""
        <div class='message-row user'>
            <div class='avatar avatar-user'>👤</div>
            <div class='bubble bubble-user'>{msg['content']}</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class='message-row nexus'>
            <div class='avatar avatar-nexus'>✦</div>
            <div class='bubble bubble-nexus'>{msg['content']}</div>
        </div>""", unsafe_allow_html=True)

# Botão limpar
if st.session_state.messages:
    col1, col2, col3 = st.columns([4, 2, 4])
    with col2:
        if st.button("🗑️ Nova conversa", key="clear"):
            st.session_state.messages = []
            st.rerun()

# ─────────────────────────────────────────────
# Input
# ─────────────────────────────────────────────
pergunta = st.chat_input("Pergunte qualquer coisa ao Nexus IA...", key="input")

if pergunta:
    st.session_state.messages.append({"role": "user", "content": pergunta})
    st.markdown(f"""
    <div class='message-row user'>
        <div class='avatar avatar-user'>👤</div>
        <div class='bubble bubble-user'>{pergunta}</div>
    </div>""", unsafe_allow_html=True)

    historico = []
    for msg in st.session_state.messages[:-1]:
        if msg["role"] == "user":
            historico.append(HumanMessage(content=msg["content"]))
        else:
            historico.append(AIMessage(content=msg["content"]))

    with st.spinner(""):
        chain = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ]) | llm
        try:
            resposta = chain.invoke({"history": historico, "question": pergunta})
            conteudo = resposta.content
        except Exception as e:
            conteudo = f"❌ Erro: {e}"

    st.session_state.messages.append({"role": "assistant", "content": conteudo})
    st.markdown(f"""
    <div class='message-row nexus'>
        <div class='avatar avatar-nexus'>✦</div>
        <div class='bubble bubble-nexus'>{conteudo}</div>
    </div>""", unsafe_allow_html=True)
