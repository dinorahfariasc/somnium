import streamlit as st
import asyncio
import ollama
import os
import sys
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.session import ClientSession

# --- Configuração da Página ---
st.set_page_config(
    page_title="Somnium Oneiros", 
    page_icon="🌙", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização Customizada (CSS)
st.markdown("""
<style>
    .main {background-color: #0e1117;}
    h1 {color: #9d4edd; text-align: center;}
    .stTextArea textarea {font-size: 16px; border-radius: 10px;}
    .stButton button {background-color: #9d4edd; color: white; border-radius: 20px;}
    div[data-testid="stToast"] {background-color: #2b2d42; color: white;}
</style>
""", unsafe_allow_html=True)

# --- Cabeçalho ---
st.title("🌙 Somnium: Intérprete de Sonhos")
st.markdown("<p style='text-align: center; color: #8d99ae;'>RAG Simbólico + Memória Pessoal + Visão Artística (DALL-E 3)</p>", unsafe_allow_html=True)
st.divider()

# --- Layout ---
col_input, col_result = st.columns([1, 1.2])

with col_input:
    st.subheader("📝 Seu Sonho de Hoje")
    relato = st.text_area("Descreva com detalhes o que você viu...", height=250, placeholder="Ex: Estava caminhando em uma floresta de vidro e encontrei uma coruja azul...")
    
    # Opções
    modelo_llm = st.selectbox("Modelo de Análise (Ollama)", ["llama3", "mistral", "gemma"], index=0, help="Escolha qual 'cérebro' vai analisar os dados.")
    
    analisar_btn = st.button("🔮 Interpretar Sonho", type="primary", use_container_width=True)

# --- Função Async para Conversar com o Servidor MCP ---
async def processar_sonho_completo(texto_sonho):
    # 1. Configura a conexão com seu server.py
    server_params = StdioServerParameters(command="python", args=["server.py"])
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Passo A: Ler Memória (Opcional, mas bom pra contexto)
            st.toast("🧠 Acessando memória...", icon="📖")
            try:
                res_hist = await session.call_tool("ler_historico_pessoal")
                historico = res_hist.content[0].text
            except:
                historico = "Sem histórico disponível."

            # Passo B: Consultar RAG
            st.toast("📚 Consultando livros de símbolos...", icon="🔍")
            res_rag = await session.call_tool("consultar_significado_onirico", arguments={"relato_sonho": texto_sonho})
            contexto_rag = res_rag.content[0].text
            
            # Passo C: Gerar Imagem
            st.toast("🎨 Pintando o sonho...", icon="🖌️")
            prompt_visual = f"Artistic dream representation: {texto_sonho}"
            res_img = await session.call_tool("gerar_imagem_do_sonho", arguments={"descricao_visual": prompt_visual})
            msg_imagem = res_img.content[0].text
            
            return historico, contexto_rag, msg_imagem

# --- Lógica Principal ---
if analisar_btn and relato:
    with col_result:
        st.subheader("✨ Análise Onírica")
        container_analise = st.container()
        
        with st.spinner("Conectando aos agentes neurais..."):
            try:
                # 1. Executa o MCP (Python)
                historia, dados_rag, info_img = asyncio.run(processar_sonho_completo(relato))
                
                # 2. Exibe a Imagem (se tiver sido gerada)
                # O servidor retorna algo como "Imagem gerada e salva em: /caminho/sonho_atual.png"
                if "salva em:" in info_img:
                    caminho = info_img.split("salva em: ")[1].strip()
                    if os.path.exists(caminho):
                        st.image(caminho, caption="Visão do Inconsciente (DALL-E 3)", use_column_width=True)
                    else:
                        st.warning("Imagem gerada, mas arquivo não encontrado.")
                else:
                    st.error(f"Erro na imagem: {info_img}")

                # 3. Gera o Texto Final (Ollama)
                prompt_final = f"""
                Você é o Somnium, um analista de sonhos sábio e empático.
                
                DADOS DO RAG (Simbologia):
                {dados_rag}
                
                HISTÓRICO DO SONHADOR:
                {historia}
                
                SONHO ATUAL:
                "{relato}"
                
                TAREFA:
                Faça uma interpretação psicológica junguiana. 
                1. Analise os símbolos encontrados.
                2. Conecte com o histórico se houver padrão.
                3. Dê um conselho curto.
                """
                
                st.markdown("### 🧠 Interpretação")
                res_box = st.empty()
                texto_completo = ""
                
                # Streaming da resposta
                stream = ollama.chat(model=modelo_llm, messages=[{'role': 'user', 'content': prompt_final}], stream=True)
                for chunk in stream:
                    texto_completo += chunk['message']['content']
                    res_box.markdown(texto_completo)
                
                st.success("Análise concluída!")

            except Exception as e:
                st.error(f"Falha no sistema: {e}")
                st.info("Dica: Verifique se o `ollama serve` está rodando e se sua chave OpenAI está correta no `server.py`.")

elif analisar_btn and not relato:
    st.toast("Por favor, digite seu sonho primeiro!", icon="⚠️")