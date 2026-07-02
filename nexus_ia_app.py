import os
import json
import base64
import io
import re
import urllib.parse
import uuid
import streamlit as st
from datetime import datetime
from groq import Groq
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from pypdf import PdfReader
from docx import Document as DocxDocument
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from duckduckgo_search import DDGS
from supabase import create_client, Client

# ─────────────────────────────────────────────
# Configuração de segredos (Streamlit Cloud > Settings > Secrets)
# Nunca deixe chaves escritas direto no código!
# ─────────────────────────────────────────────
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
ADMIN_EMAIL = st.secrets.get("ADMIN_EMAIL", "")  # seu e-mail, para ver o painel de usuários

st.set_page_config(
    page_title="Nexus IA – Seu Assistente Inteligente",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("⚠️ Configure SUPABASE_URL e SUPABASE_KEY em Settings → Secrets do Streamlit Cloud.")
    st.stop()

if not GROQ_API_KEY:
    st.error("⚠️ Configure GROQ_API_KEY em Settings → Secrets do Streamlit Cloud.")
    st.stop()

@st.cache_resource(show_spinner=False)
def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

# ─────────────────────────────────────────────
# CSS Premium – Identidade Nexus IA
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    html, body, .stApp { background: #0a0e27; font-family: 'Inter', sans-serif; color: #e2e8f0; }
    #MainMenu, footer { visibility: hidden; }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stToolbar"] { visibility: hidden; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0f1434 0%, #0a0e27 100%); border-right: 1px solid #1e1e3f; }
    [data-testid="stSidebarContent"] { padding: 0.5rem 0.5rem; }
    .sidebar-logo { width: 56px; height: 56px; border-radius: 16px; overflow: hidden; background: #0f0f1e;
        display: flex; align-items: center; justify-content: center; font-size: 1.5rem; margin: 1rem auto 1.5rem auto;
        box-shadow: 0 0 30px rgba(139, 92, 246, 0.4), 0 0 60px rgba(99, 102, 241, 0.15); animation: pulse-glow 3s ease-in-out infinite; }
    @keyframes pulse-glow { 0%,100% { box-shadow: 0 0 30px rgba(139,92,246,0.4), 0 0 60px rgba(99,102,241,0.15);} 50% { box-shadow: 0 0 45px rgba(139,92,246,0.6), 0 0 90px rgba(99,102,241,0.25);} }
    .sidebar-logo img { width: 100%; height: 100%; object-fit: cover; }
    .conversation-item { background: #0f1434; border: 1px solid #1e1e3f; border-radius: 12px; padding: 12px; margin-bottom: 10px;
        cursor: pointer; transition: all 0.3s ease; font-size: 0.85rem; color: #94a3b8; line-height: 1.3; max-height: 60px; overflow: hidden; }
    .conversation-item:hover { background: #1a1f3a; border-color: #6366f1; color: #cbd5e1; }
    .block-container { padding-top: 1rem; padding-bottom: 5rem; max-width: 1600px; }
    .nexus-hero { text-align: center; padding: 2rem 1rem 1rem 1rem; margin-bottom: 1.5rem; }
    .nexus-logo { width: 72px; height: 72px; border-radius: 20px; overflow: hidden; background: #0f0f1e; display: inline-flex;
        align-items: center; justify-content: center; font-size: 2rem; margin-bottom: 1rem;
        box-shadow: 0 0 40px rgba(139, 92, 246, 0.5), 0 0 80px rgba(99, 102, 241, 0.2); animation: pulse-glow 3s ease-in-out infinite; }
    .nexus-title { font-size: 2.2rem; font-weight: 800; letter-spacing: -0.03em;
        background: linear-gradient(90deg, #a78bfa, #818cf8, #38bdf8, #34d399);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin: 0; line-height: 1.1; }
    .nexus-subtitle { color: #64748b; font-size: 0.9rem; margin-top: 0.5rem; font-weight: 400; letter-spacing: 0.04em; }
    .message-row { display: flex; align-items: flex-end; gap: 10px; margin-bottom: 1rem; animation: slideIn 0.25s ease-out; }
    @keyframes slideIn { from { opacity: 0; transform: translateY(10px);} to { opacity: 1; transform: translateY(0);} }
    .message-row.user { flex-direction: row-reverse; }
    .message-row.nexus { flex-direction: row; }
    .avatar { width: 34px; height: 34px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center;
        font-size: 1rem; flex-shrink: 0; overflow: hidden; }
    .avatar-nexus { background: #0f0f1e; box-shadow: 0 0 12px rgba(139,92,246,0.5); }
    .avatar-user { background: linear-gradient(135deg, #0f172a, #1e293b); border: 1px solid #334155; }
    .bubble { padding: 13px 18px; border-radius: 18px; max-width: 85%; font-size: 0.925rem; line-height: 1.7; word-wrap: break-word; }
    .bubble-nexus { background: linear-gradient(135deg, #0f0f1e, #12122a); border: 1px solid #1e1e3f; border-bottom-left-radius: 4px; color: #e2e8f0; }
    .bubble-user { background: linear-gradient(135deg, #312e81, #3730a3); border: 1px solid #4338ca; border-bottom-right-radius: 4px; color: #eef2ff; }
    .attachment-img { max-width: 220px; max-height: 220px; border-radius: 12px; margin-bottom: 8px; display: block; object-fit: cover; }
    .attachment-doc { display: inline-flex; align-items: center; gap: 6px; background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.15);
        border-radius: 10px; padding: 6px 12px; margin-bottom: 8px; font-size: 0.8rem; }
    .generated-img { max-width: 100%; width: 380px; border-radius: 14px; margin-bottom: 4px; display: block; border: 1px solid #1e1e3f; }
    [data-testid="stDownloadButton"] button { background: transparent !important; border: 1px solid #1e1e3f !important; color: #94a3b8 !important;
        border-radius: 10px !important; font-size: 0.78rem !important; padding: 4px 12px !important; margin-top: -8px; margin-bottom: 12px; }
    [data-testid="stDownloadButton"] button:hover { border-color: #6366f1 !important; color: #a78bfa !important; background: rgba(99, 102, 241, 0.1) !important; }
    [data-testid="stChatInput"] textarea { background: #0f0f1e !important; border: 1px solid #1e1e3f !important; border-radius: 16px !important;
        color: #e2e8f0 !important; font-family: 'Inter', sans-serif !important; font-size: 0.93rem !important; padding: 14px 18px !important; }
    [data-testid="stChatInput"] textarea:focus { border-color: #6366f1 !important; box-shadow: 0 0 0 3px rgba(99,102,241,0.2) !important; }
    [data-testid="stChatInput"] { background: #12122a !important; border-radius: 18px !important; }
    [data-testid="stChatInput"] > div { background: #12122a !important; border: 1px solid #1e1e3f !important; border-radius: 18px !important; }
    [data-testid="stChatInputSubmitButton"] { background: #1e1e3f !important; border-radius: 12px !important; }
    [data-testid="stChatInputSubmitButton"]:hover { background: #6366f1 !important; }
    [data-testid="stChatInputSubmitButton"] svg { fill: #cbd5e1 !important; }
    .stSpinner > div { border-top-color: #8b5cf6 !important; }
    .stButton > button { background: transparent; border: 1px solid #1e1e3f; color: #64748b !important; border-radius: 10px;
        font-size: 0.82rem; padding: 8px 16px; transition: all 0.2s; width: 100%; }
    .stButton > button:hover { border-color: #6366f1; color: #a78bfa !important; background: rgba(99, 102, 241, 0.1); }
    .history-header { font-size: 0.75rem; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;
        margin-top: 1.5rem; margin-bottom: 1rem; padding: 0 0.5rem; }
    .empty-state { text-align: center; padding: 1rem; color: #475569; font-size: 0.85rem; }
    .admin-badge { background: rgba(52,211,153,0.1); border: 1px solid #34d399; color: #34d399; border-radius: 10px;
        padding: 8px 12px; font-size: 0.8rem; text-align: center; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

LOGO_URL = "https://raw.githubusercontent.com/TaianeR/nexus-ia/main/logo.png"

# ═════════════════════════════════════════════
# AUTENTICAÇÃO
# ═════════════════════════════════════════════
if "user" not in st.session_state:
    st.session_state.user = None

def tela_login():
    st.markdown(f"""
    <div class="nexus-hero">
        <div class="nexus-logo"><img src="{LOGO_URL}" style="width:100%;height:100%;object-fit:cover;"></div>
        <h1 class="nexus-title">Nexus IA</h1>
        <p class="nexus-subtitle">Entre com seu e-mail para continuar</p>
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([1, 1.2, 1])
    with col_b:
        aba_login, aba_cadastro = st.tabs(["Entrar", "Criar conta"])

        with aba_login:
            email = st.text_input("E-mail", key="login_email")
            senha = st.text_input("Senha", type="password", key="login_senha")
            if st.button("Entrar", use_container_width=True, key="btn_login"):
                try:
                    resultado = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                    st.session_state.user = {"id": resultado.user.id, "email": resultado.user.email}
                    st.rerun()
                except Exception as e:
                    st.error(f"Não foi possível entrar: {e}")

        with aba_cadastro:
            novo_email = st.text_input("E-mail", key="cad_email")
            nova_senha = st.text_input("Senha (mínimo 6 caracteres)", type="password", key="cad_senha")
            if st.button("Criar conta", use_container_width=True, key="btn_cadastro"):
                try:
                    resultado = supabase.auth.sign_up({"email": novo_email, "password": nova_senha})
                    if resultado.user:
                        st.success("Conta criada! Se a confirmação por e-mail estiver ativada no Supabase, verifique sua caixa de entrada antes de entrar.")
                    else:
                        st.error("Não foi possível criar a conta.")
                except Exception as e:
                    st.error(f"Erro ao criar conta: {e}")

if not st.session_state.user:
    tela_login()
    st.stop()

usuario_atual = st.session_state.user  # {"id":..., "email":...}

# ═════════════════════════════════════════════
# FUNÇÕES DE BANCO DE DADOS (Supabase)
# ═════════════════════════════════════════════
def listar_conversas(user_id):
    resp = supabase.table("conversations").select("id, title, created_at") \
        .eq("user_id", user_id).order("created_at", desc=True).execute()
    return resp.data or []

def criar_conversa(user_id, title="Nova conversa"):
    resp = supabase.table("conversations").insert({"user_id": user_id, "title": title}).execute()
    return resp.data[0]["id"]

def renomear_conversa(conversation_id, novo_titulo):
    supabase.table("conversations").update({"title": novo_titulo}).eq("id", conversation_id).execute()

def deletar_conversa_db(conversation_id):
    supabase.table("conversations").delete().eq("id", conversation_id).execute()

def carregar_mensagens(conversation_id):
    resp = supabase.table("messages").select("*").eq("conversation_id", conversation_id) \
        .order("created_at", desc=False).execute()
    mensagens = []
    for m in (resp.data or []):
        mensagens.append({
            "role": m["role"],
            "content": m["content"],
            "is_image": m.get("is_image", False),
            "attachments": m.get("attachments") or [],
        })
    return mensagens

def salvar_mensagem_db(conversation_id, user_id, role, content, is_image=False, attachments=None):
    supabase.table("messages").insert({
        "conversation_id": conversation_id,
        "user_id": user_id,
        "role": role,
        "content": content,
        "is_image": is_image,
        "attachments": attachments or [],
    }).execute()

def contar_usuarios_total():
    try:
        resp = supabase.rpc("contar_usuarios").execute()
        return resp.data
    except Exception:
        return "—"

# ─────────────────────────────────────────────
# Gerenciamento de Sessão
# ─────────────────────────────────────────────
if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "tom" not in st.session_state:
    st.session_state.tom = "informal"

def create_new_conversation():
    conversation_id = criar_conversa(usuario_atual["id"])
    st.session_state.current_conversation_id = conversation_id
    st.session_state.messages = []
    st.rerun()

def load_conversation(conversation_id):
    st.session_state.current_conversation_id = conversation_id
    st.session_state.messages = carregar_mensagens(conversation_id)
    st.rerun()

def delete_conversation(conversation_id):
    deletar_conversa_db(conversation_id)
    if st.session_state.current_conversation_id == conversation_id:
        st.session_state.current_conversation_id = None
        st.session_state.messages = []
    st.rerun()

def render_attachments(attachments):
    if not attachments:
        return ""
    html = ""
    for a in attachments:
        if a["tipo"] == "imagem":
            html += f'<img class="attachment-img" src="data:{a["mime"]};base64,{a["data"]}">'
        else:
            html += f'<div class="attachment-doc">📄 {a["nome"]}</div>'
    return html

# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown(f'<div class="sidebar-logo"><img src="{LOGO_URL}" style="width:100%;height:100%;object-fit:cover;"></div>', unsafe_allow_html=True)

    st.caption(f"👤 {usuario_atual['email']}")
    if st.button("🚪 Sair", use_container_width=True):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.session_state.current_conversation_id = None
        st.session_state.messages = []
        st.rerun()

    # Painel admin — só aparece pro e-mail configurado em ADMIN_EMAIL
    if ADMIN_EMAIL and usuario_atual["email"].lower() == ADMIN_EMAIL.lower():
        total = contar_usuarios_total()
        st.markdown(f'<div class="admin-badge">👥 Total de usuários: {total}</div>', unsafe_allow_html=True)

    st.divider()

    if st.button("➕ Nova Conversa", use_container_width=True):
        create_new_conversation()

    st.divider()
    st.markdown("<div class='history-header'>📋 Histórico</div>", unsafe_allow_html=True)

    conversas = listar_conversas(usuario_atual["id"])
    if conversas:
        for conv in conversas:
            col1, col2 = st.columns([0.85, 0.15])
            with col1:
                if st.button(f"💬 {conv['title']}", key=f"conv_{conv['id']}", use_container_width=True):
                    load_conversation(conv["id"])
            with col2:
                if st.button("🗑️", key=f"del_{conv['id']}", help="Deletar", use_container_width=True):
                    delete_conversation(conv["id"])
    else:
        st.markdown("<div class='empty-state'>Nenhuma conversa ainda</div>", unsafe_allow_html=True)

    st.divider()
    st.caption("🚀 Desenvolvido com Streamlit + Groq + Supabase")

# ─────────────────────────────────────────────
# Modelos Groq
# ─────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_llm():
    return ChatGroq(model="openai/gpt-oss-120b", temperature=0.7, max_tokens=2048, groq_api_key=GROQ_API_KEY)

@st.cache_resource(show_spinner=False)
def get_groq_client():
    return Groq(api_key=GROQ_API_KEY)

llm = get_llm()
groq_client = get_groq_client()
VISION_MODEL = "qwen/qwen3.6-27b"  # confira o nome atual do modelo na documentação da Groq

SYSTEM_PROMPT_BASE = """Você é o Nexus IA, um assistente de inteligência artificial avançado e inteligente.
Você pode ajudar com qualquer assunto: perguntas gerais, criatividade, tecnologia, conselhos,
redação, análise, programação, dúvidas do dia a dia e muito mais."""

SYSTEM_PROMPT_INFORMAL = SYSTEM_PROMPT_BASE + """
Responda sempre em português do Brasil, de forma clara, natural, descontraída e envolvente.
Seja direto, útil e use uma linguagem acessível. Use emojis com moderação quando ficarem naturais."""

SYSTEM_PROMPT_FORMAL = SYSTEM_PROMPT_BASE + """
Responda sempre em português do Brasil, em tom FORMAL e profissional: linguagem cuidada e objetiva,
sem gírias, sem emojis, frases completas, como em um ambiente corporativo/institucional."""

def montar_system_prompt():
    return SYSTEM_PROMPT_FORMAL if st.session_state.tom == "formal" else SYSTEM_PROMPT_INFORMAL

def detectar_comando_tom(texto):
    texto_limpo = re.sub(r'[.!?]+$', '', (texto or "").strip().lower())
    if re.fullmatch(r'(ativar\s+)?modo\s+formal', texto_limpo):
        return "formal"
    if re.fullmatch(r'(ativar\s+)?modo\s+informal', texto_limpo):
        return "informal"
    return None

# ─────────────────────────────────────────────
# Extração de arquivos
# ─────────────────────────────────────────────
def extrair_texto_pdf(arquivo):
    try:
        leitor = PdfReader(arquivo)
        return "\n".join(p.extract_text() or "" for p in leitor.pages).strip()
    except Exception:
        return ""

def extrair_texto_docx(arquivo):
    try:
        doc = DocxDocument(arquivo)
        return "\n".join(p.text for p in doc.paragraphs).strip()
    except Exception:
        return ""

def processar_arquivos(arquivos):
    imagens, textos_extraidos, anexos_display = [], [], []
    for arquivo in arquivos:
        nome, tipo = arquivo.name, arquivo.type or ""
        if tipo.startswith("image/"):
            bytes_img = arquivo.read()
            b64 = base64.b64encode(bytes_img).decode("utf-8")
            imagens.append({"mime": tipo, "data": b64})
            anexos_display.append({"tipo": "imagem", "nome": nome, "data": b64, "mime": tipo})
        elif nome.lower().endswith(".pdf"):
            conteudo = extrair_texto_pdf(arquivo)
            if conteudo:
                textos_extraidos.append(f"[Conteúdo do arquivo '{nome}']:\n{conteudo[:8000]}")
            anexos_display.append({"tipo": "documento", "nome": nome})
        elif nome.lower().endswith(".docx"):
            conteudo = extrair_texto_docx(arquivo)
            if conteudo:
                textos_extraidos.append(f"[Conteúdo do arquivo '{nome}']:\n{conteudo[:8000]}")
            anexos_display.append({"tipo": "documento", "nome": nome})
        elif nome.lower().endswith(".txt"):
            conteudo = arquivo.read().decode("utf-8", errors="ignore")
            if conteudo:
                textos_extraidos.append(f"[Conteúdo do arquivo '{nome}']:\n{conteudo[:8000]}")
            anexos_display.append({"tipo": "documento", "nome": nome})
        else:
            anexos_display.append({"tipo": "documento", "nome": nome})
    return imagens, textos_extraidos, anexos_display

# ─────────────────────────────────────────────
# Geração de imagens
# ─────────────────────────────────────────────
PADROES_PEDIDO_IMAGEM = [
    r'\b(crie?|gere?|desenh[ae]|fa[çc]a|cri[ae])\s+(uma|um)?\s*imagem\b',
    r'\bimagem\s+de\b', r'\bgerar\s+imagem\b', r'\bgera\s+(uma\s+)?imagem\b',
    r'\brecri[ae]\b', r'\brefa[çc]a\s+(a|essa|esta)?\s*imagem\b', r'\btransform[ea]\s+(a|essa|esta)?\s*imagem\b',
]

def eh_pedido_de_imagem(texto):
    texto_lower = (texto or "").lower()
    return any(re.search(p, texto_lower) for p in PADROES_PEDIDO_IMAGEM)

def gerar_imagem(prompt):
    prompt_encoded = urllib.parse.quote(prompt.strip()[:500])
    semente = datetime.now().strftime("%H%M%S")
    return f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=768&height=768&nologo=true&seed={semente}"

# ─────────────────────────────────────────────
# Pesquisa Web via DuckDuckGo
# ─────────────────────────────────────────────
def pesquisar_na_web(termo_busca, max_resultados=3):
    try:
        with DDGS() as ddgs:
            resultados = [r for r in ddgs.text(termo_busca, max_results=max_resultados)]
            if not resultados:
                return ""
            contexto = "\n\n--- INFORMAÇÕES PESQUISADAS EM TEMPO REAL NA WEB ---\n"
            for r in resultados:
                contexto += f"Título: {r['title']}\nLink: {r['href']}\nResumo: {r['body']}\n\n"
            return contexto
    except Exception:
        return ""

# ─────────────────────────────────────────────
# Relatório em PDF
# ─────────────────────────────────────────────
def limpar_pensamento(texto):
    if not texto:
        return texto
    texto = re.sub(r'<think>.*?</think>', '', texto, flags=re.DOTALL | re.IGNORECASE)
    texto = re.sub(r'<reasoning>.*?</reasoning>', '', texto, flags=re.DOTALL | re.IGNORECASE)
    return texto.strip()

def gerar_pdf_relatorio(titulo, texto):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm)
    estilos = getSampleStyleSheet()
    elementos = [Paragraph(titulo, estilos["Title"]), Spacer(1, 14)]
    texto_limpo = re.sub(r'<[^>]+>', '', texto or "")
    for paragrafo in texto_limpo.split("\n"):
        paragrafo = paragrafo.strip()
        if paragrafo:
            seguro = paragrafo.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            elementos.append(Paragraph(seguro, estilos["Normal"]))
            elementos.append(Spacer(1, 8))
    doc.build(elementos)
    buffer.seek(0)
    return buffer.getvalue()

# ─────────────────────────────────────────────
# Tela inicial (sem conversa aberta)
# ─────────────────────────────────────────────
col1, col2, col3 = st.columns([1, 5, 1])
with col2:
    if not st.session_state.current_conversation_id:
        st.markdown(f"""
        <div class="nexus-hero">
            <div class="nexus-logo"><img src="{LOGO_URL}" style="width:100%;height:100%;object-fit:cover;"></div>
            <h1 class="nexus-title">Nexus IA</h1>
            <p class="nexus-subtitle">Inteligência Artificial · Sempre pronto para te ajudar</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Começar Conversa", use_container_width=True, key="start_conv"):
            create_new_conversation()

# ─────────────────────────────────────────────
# Chat Interface
# ─────────────────────────────────────────────
if st.session_state.current_conversation_id:
    with col2:
        for idx_msg, msg in enumerate(st.session_state.messages):
            anexos_html = render_attachments(msg.get("attachments"))
            if msg["role"] == "user":
                st.markdown(f"""
                <div class='message-row user'>
                    <div class='avatar avatar-user'>👤</div>
                    <div class='bubble bubble-user'>{anexos_html}{msg['content']}</div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class='message-row nexus'>
                    <div class='avatar avatar-nexus'><img src="{LOGO_URL}" style="width:100%;height:100%;object-fit:cover;"></div>
                    <div class='bubble bubble-nexus'>{anexos_html}{msg['content']}</div>
                </div>""", unsafe_allow_html=True)
                if not msg.get("is_image") and msg.get("content"):
                    pdf_bytes = gerar_pdf_relatorio("Relatório - Nexus IA", msg["content"])
                    st.download_button("📥 Baixar como PDF", data=pdf_bytes,
                        file_name=f"relatorio_nexus_{idx_msg}.pdf", mime="application/pdf", key=f"pdf_hist_{idx_msg}")

        entrada = st.chat_input(
            "Pergunte qualquer coisa ao Nexus IA...",
            accept_file="multiple",
            file_type=["png", "jpg", "jpeg", "webp", "pdf", "docx", "txt"],
            key="input",
        )

        if entrada:
            pergunta = entrada.text or ""
            arquivos = entrada.files or []
            imagens, textos_extraidos, anexos_display = processar_arquivos(arquivos)

            st.session_state.messages.append({"role": "user", "content": pergunta, "attachments": anexos_display})
            salvar_mensagem_db(st.session_state.current_conversation_id, usuario_atual["id"], "user", pergunta, False, anexos_display)

            anexos_html_novo = render_attachments(anexos_display)
            st.markdown(f"""
            <div class='message-row user'>
                <div class='avatar avatar-user'>👤</div>
                <div class='bubble bubble-user'>{anexos_html_novo}{pergunta}</div>
            </div>""", unsafe_allow_html=True)

            prompt_final = pergunta
            if textos_extraidos:
                prompt_final = (prompt_final + "\n\n" + "\n\n".join(textos_extraidos)).strip()
            if not prompt_final:
                prompt_final = "Descreva o que você vê." if imagens else "Analise o conteúdo enviado."

            with st.spinner(""):
                is_image_flag = False
                try:
                    comando_tom = detectar_comando_tom(pergunta)
                    pedido_imagem = eh_pedido_de_imagem(pergunta)

                    if comando_tom:
                        st.session_state.tom = comando_tom
                        conteudo = ("✅ Modo **formal** ativado. A partir de agora, responderei de forma profissional e objetiva."
                                    if comando_tom == "formal" else
                                    "✅ Modo **informal** ativado! A partir de agora vou responder de um jeito mais leve e descontraído 😊")

                    elif pedido_imagem and imagens:
                        content_msgs = [{"type": "text", "text": "Descreva esta imagem em detalhes, em inglês, em uma única frase, para ser usada como prompt de um gerador de imagens."}]
                        for img in imagens:
                            content_msgs.append({"type": "image_url", "image_url": {"url": f"data:{img['mime']};base64,{img['data']}"}})
                        descricao_resp = groq_client.chat.completions.create(
                            model=VISION_MODEL, messages=[{"role": "user", "content": content_msgs}],
                            reasoning_effort="none", reasoning_format="hidden")
                        descricao = descricao_resp.choices[0].message.content
                        url_imagem = gerar_imagem(f"{descricao}. {pergunta}")
                        conteudo = f'<img class="generated-img" src="{url_imagem}">'
                        is_image_flag = True

                    elif pedido_imagem and not arquivos:
                        url_imagem = gerar_imagem(pergunta)
                        conteudo = f'<img class="generated-img" src="{url_imagem}">'
                        is_image_flag = True

                    elif imagens:
                        content_msgs = [{"type": "text", "text": prompt_final}]
                        for img in imagens:
                            content_msgs.append({"type": "image_url", "image_url": {"url": f"data:{img['mime']};base64,{img['data']}"}})
                        resposta = groq_client.chat.completions.create(
                            model=VISION_MODEL,
                            messages=[{"role": "system", "content": montar_system_prompt()}, {"role": "user", "content": content_msgs}],
                            reasoning_effort="none", reasoning_format="hidden")
                        conteudo = resposta.choices[0].message.content

                    else:
                        historico = []
                        for msg in st.session_state.messages[:-1]:
                            if msg["role"] == "user":
                                historico.append(HumanMessage(content=msg["content"]))
                            else:
                                historico.append(AIMessage(content=msg["content"]))

                        indicadores_busca = ["hoje", "noticia", "notícia", "quem é", "quem foi", "resultado", "jogo",
                                              "atual", "tempo", "clima", "preço", "dolar", "euro", "últimas", "ultimas",
                                              "pesquise", "busca", "quando", "onde fica", "quanto custa"]
                        contexto_web = ""
                        if any(palavra in pergunta.lower() for palavra in indicadores_busca):
                            with st.spinner("🔍 Pesquisando na internet por informações atualizadas..."):
                                termo_filtrado = re.sub(r'\b(pesquise|procure|busque|no google|na internet|sobre)\b', '', pergunta, flags=re.IGNORECASE).strip()
                                contexto_web = pesquisar_na_web(termo_filtrado if termo_filtrado else pergunta)

                        prompt_com_web = prompt_final
                        if contexto_web:
                            prompt_com_web += f"\n\nUse estas informações coletadas da internet em tempo real caso sejam relevantes:\n{contexto_web}"

                        chain = ChatPromptTemplate.from_messages([
                            ("system", montar_system_prompt()),
                            MessagesPlaceholder(variable_name="history"),
                            ("human", "{question}"),
                        ]) | llm
                        resposta = chain.invoke({"history": historico, "question": prompt_com_web})
                        conteudo = resposta.content
                except Exception as e:
                    conteudo = f"❌ Erro: {e}"

                if not is_image_flag:
                    conteudo = limpar_pensamento(conteudo)

            st.session_state.messages.append({"role": "assistant", "content": conteudo, "is_image": is_image_flag})
            salvar_mensagem_db(st.session_state.current_conversation_id, usuario_atual["id"], "assistant", conteudo, is_image_flag)

            # Renomeia a conversa com a primeira pergunta, se ainda estiver com o título padrão
            if len(st.session_state.messages) == 2 and pergunta:
                novo_titulo = pergunta[:50] + ("..." if len(pergunta) > 50 else "")
                renomear_conversa(st.session_state.current_conversation_id, novo_titulo)

            st.markdown(f"""
            <div class='message-row nexus'>
                <div class='avatar avatar-nexus'><img src="{LOGO_URL}" style="width:100%;height:100%;object-fit:cover;"></div>
                <div class='bubble bubble-nexus'>{conteudo}</div>
            </div>""", unsafe_allow_html=True)

            if not is_image_flag:
                pdf_bytes_novo = gerar_pdf_relatorio("Relatório - Nexus IA", conteudo)
                st.download_button("📥 Baixar como PDF", data=pdf_bytes_novo,
                    file_name="relatorio_nexus_novo.pdf", mime="application/pdf", key="pdf_novo")
            st.rerun()
