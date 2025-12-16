import sys
import os
import pandas as pd
import numpy as np
import faiss
from mcp.server.fastmcp import FastMCP
from sentence_transformers import SentenceTransformer
from openai import OpenAI # Biblioteca oficial
import dotenv
import requests
import dotenv
import datetime

# --- Configuração Inicial ---
print("Iniciando Servidor Somnium MCP...", file=sys.stderr)

# ⚠️ COLOQUE SUA CHAVE AQUI ⚠️
dotenv.load_dotenv()  # Carrega variáveis do .env 
API_KEY = os.getenv("API_OPENAI")


INDEX_PATH = "faiss_index.idx"
DATA_PATH = "base_sonhos_rag.parquet"
DIARIO_PATH = "diario_sonhos.txt"

embedding_model = None
index = None
corpus = None

def carregar_modelos_texto():
    global embedding_model, index, corpus
    if embedding_model is None:
        print("Carregando modelo E5...", file=sys.stderr)
        embedding_model = SentenceTransformer("intfloat/multilingual-e5-base")
    if index is None and os.path.exists(INDEX_PATH):
        print("Carregando índice FAISS...", file=sys.stderr)
        index = faiss.read_index(INDEX_PATH)
    if corpus is None and os.path.exists(DATA_PATH):
        print("Carregando dados do corpus...", file=sys.stderr)
        corpus = pd.read_parquet(DATA_PATH)

mcp = FastMCP("Somnium Agent")

try:
    carregar_modelos_texto()
    print("SISTEMA PRONTO.", file=sys.stderr)
except Exception as e:
    print(f"Erro ao carregar: {e}", file=sys.stderr)

# --- Ferramenta 1: RAG ---
@mcp.tool()
def consultar_significado_onirico(relato_sonho: str) -> str:
    """Consulta a base de conhecimento de símbolos usando RAG."""
    if index is None or corpus is None: return "Erro: Dados não carregados."
    query_emb = embedding_model.encode(relato_sonho, convert_to_tensor=False, normalize_embeddings=True, show_progress_bar=False).reshape(1, -1)
    distances, indices = index.search(query_emb, 3)
    resposta = f"--- Análise Simbólica ---\n"
    for i, idx in enumerate(indices[0]):
        if idx == -1: continue
        item = corpus.iloc[idx]
        texto = item.get('texto_lemas', item.get('sonho_original', 'Trecho'))
        sig = item.get('significado', item.get('interpretacao', '...'))
        resposta += f"[Top {i+1}] {str(texto)[:50]}... -> {sig}\n"
    return resposta

# --- Ferramenta 2: Leitura de Memória ---
@mcp.tool()
def ler_historico_pessoal() -> str:
    """Lê o diário de sonhos do usuário."""
    if not os.path.exists(DIARIO_PATH): return "Diário vazio."
    with open(DIARIO_PATH, "r", encoding="utf-8") as f:
        return f"--- Histórico Recente ---\n{f.read()}"

# --- Ferramenta 3: Escrita de Memória (NOVA!) ---
@mcp.tool()
def salvar_sonho_no_diario(relato: str) -> str:
    """Salva o novo sonho no arquivo txt com a data de hoje."""
    try:
        data_hoje = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        novo_registro = f"\n\nData: {data_hoje}\nSonho: {relato}\n"
        
        # O modo 'a' (append) adiciona ao final sem apagar o que já tem
        with open(DIARIO_PATH, "a", encoding="utf-8") as f:
            f.write(novo_registro)
            
        print(f"Sonho salvo em {DIARIO_PATH}", file=sys.stderr)
        return "Sonho registrado com sucesso no diário."
    except Exception as e:
        return f"Erro ao salvar sonho: {e}"

# --- Ferramenta 4: Imagem (DALL-E) ---
@mcp.tool()
def gerar_imagem_do_sonho(descricao_visual: str) -> str:
    """Gera imagem realista via OpenAI."""
    # Tratamento de segurança simplificado
    prompt_safe = descricao_visual
    for bad in ["surra", "sangue", "morte", "matar"]:
        if bad in prompt_safe.lower(): prompt_safe = "intense mystery, dark shadows, abstract conflict"
    
    url = "https://api.openai.com/v1/images/generations"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
    data = {"model": "dall-e-3", "prompt": f"Photorealistic, cinematic: {prompt_safe}", "n": 1, "size": "1024x1024"}
    
    try:
        print("Gerando imagem...", file=sys.stderr)
        resp = requests.post(url, headers=headers, json=data)
        if resp.status_code != 200: 
            # Fallback rápido para DALL-E 2 se o 3 falhar
            data["model"] = "dall-e-2"; data["size"] = "512x512"
            resp = requests.post(url, headers=headers, json=data)
            if resp.status_code != 200: return "Erro na geração de imagem."
            
        img_url = resp.json()['data'][0]['url']
        img_bytes = requests.get(img_url).content
        with open("sonho_atual.png", "wb") as f: f.write(img_bytes)
        return f"Imagem salva em: {os.path.abspath('sonho_atual.png')}"
    except Exception as e: return f"Erro: {e}"

if __name__ == "__main__":
    mcp.run()