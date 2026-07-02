# Nexus IA 🤖
# ✦ Nexus IA

Assistente de inteligência artificial desenvolvido com **Streamlit**, **Groq** e **Supabase**, com login por e-mail, histórico de conversas permanente, geração de imagens, leitura de documentos e pesquisa em tempo real na web.

🔗 **App:** [nexus-ia-bot.streamlit.app](https://nexus-ia-bot.streamlit.app)

---

## ✨ Funcionalidades

- 🔐 **Login por e-mail** — cada usuário cria sua própria conta e acessa seu histórico de forma privada
- 👥 **Painel de administração** — contador do total de usuários cadastrados, visível apenas para o administrador
- 💾 **Histórico permanente** — conversas salvas em banco de dados (Supabase/Postgres), não se perdem ao reiniciar o app
- 🎭 **Tom de resposta ajustável** — alterne entre modo formal e informal a qualquer momento digitando "modo formal" ou "modo informal"
- 🌐 **Pesquisa em tempo real na web** — respostas sobre notícias, preços, resultados e eventos atuais são enriquecidas com busca ao vivo (DuckDuckGo)
- 📄 **Leitura de documentos** — envie arquivos PDF, DOCX ou TXT e converse sobre o conteúdo
- 🖼️ **Geração de imagens** — crie imagens a partir de descrições em texto, com opção de download
- 🔍 **Análise de imagens** — envie fotos para o Nexus IA descrever ou recriar
- 📥 **Relatórios em PDF** — baixe qualquer resposta de texto formatada como PDF

---

## 🛠️ Tecnologias utilizadas

| Camada | Tecnologia |
|---|---|
| Interface | Streamlit |
| Modelo de linguagem | Groq (`openai/gpt-oss-120b`) + LangChain |
| Modelo de visão | Groq (`qwen/qwen3.6-27b`) |
| Autenticação e banco de dados | Supabase (Auth + Postgres) |
| Geração de imagens | Pollinations.ai |
| Pesquisa na web | DuckDuckGo Search |
| Leitura de arquivos | pypdf, python-docx |
| Geração de PDF | ReportLab |

---

## ⚙️ Configuração do projeto

### 1. Pré-requisitos
- Conta gratuita na [Groq](https://console.groq.com) (chave de API)
- Conta gratuita no [Supabase](https://supabase.com) (banco de dados + autenticação)

### 2. Banco de dados
Rode o script `supabase_schema.sql` no **SQL Editor** do Supabase para criar as tabelas de perfis, conversas e mensagens, já com as políticas de segurança (Row Level Security) configuradas.

### 3. Variáveis de ambiente (Secrets)
No Streamlit Cloud, configure em **Settings → Secrets**:

```toml
GROQ_API_KEY = "sua-chave-da-groq"
SUPABASE_URL = "https://seu-projeto.supabase.co"
SUPABASE_KEY = "sua-chave-publishable-do-supabase"
ADMIN_EMAIL = "seu-email@exemplo.com"
```

> `ADMIN_EMAIL` define qual conta enxerga o painel com o total de usuários cadastrados.

### 4. Dependências
```
pip install -r requirements.txt
```

### 5. Rodar localmente
```
streamlit run nexus_ia_app.py
```

---

## 📁 Estrutura do projeto

```
nexus_ia_app.py       → aplicação principal (Streamlit)
supabase_schema.sql    → schema do banco de dados (rodar uma vez no Supabase)
requirements.txt       → dependências Python
```

---

## 🔒 Segurança

- Cada usuário só acessa suas próprias conversas (Row Level Security no Supabase)
- Chaves de API nunca ficam expostas no código — são carregadas via Secrets do Streamlit Cloud
- Senhas são gerenciadas inteiramente pelo Supabase Auth (nunca armazenadas em texto puro pela aplicação)

---

## 👩‍💻 Autora

Desenvolvido por **Taiane Ribas da Silveira** — TCell Assistência Técnica.
