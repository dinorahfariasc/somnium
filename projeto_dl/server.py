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

# --- Configuração Inicial ---
print("Iniciando Servidor Somnium MCP...", file=sys.stderr)

# ⚠️ COLOQUE SUA CHAVE AQUI ⚠️
dotenv.load_dotenv()  # Carrega variáveis do .env 
API_KEY = os.getenv("API_OPENAI")


INDEX_PATH = "faiss_index.idx"
DATA_PATH = "base_sonhos_rag.parquet"
DIARIO_PATH = "diario_sonhos.txt"

# Variáveis globais
embedding_model = None
index = None
corpus = None

# --- Funções de Carregamento ---
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

# --- Inicialização ---
mcp = FastMCP("Somnium Agent")

try:
    carregar_modelos_texto()
    print("SISTEMA PRONTO: Texto carregado.", file=sys.stderr)
except Exception as e:
    print(f"Erro ao carregar: {e}", file=sys.stderr)


# --- Ferramenta 1: RAG (Texto) ---
@mcp.tool()
def consultar_significado_onirico(relato_sonho: str) -> str:
    """Consulta a base de conhecimento de símbolos usando RAG."""
    if index is None or corpus is None:
        return "Erro: Arquivos de dados não encontrados."

    query_emb = embedding_model.encode(
        relato_sonho, 
        convert_to_tensor=False, 
        normalize_embeddings=True,
        show_progress_bar=False 
    ).reshape(1, -1)

    distances, indices = index.search(query_emb, 3)

    resposta_final = f"--- Análise Simbólica para: '{relato_sonho}' ---\n"
    for i, idx_corpus in enumerate(indices[0]):
        if idx_corpus == -1: continue
        item = corpus.iloc[idx_corpus]
        texto_ref = item.get('texto_lemas', item.get('sonho_original', 'Trecho'))
        significado = item.get('significado', item.get('interpretacao', 'Verificar base'))
        score = distances[0][i]
        resposta_final += f"\n[Top {i+1} | Score: {score:.2f}]\n"
        resposta_final += f"Referência: {str(texto_ref)[:100]}...\n"
        resposta_final += f"Significado: {significado}\n"

    return resposta_final


# --- Ferramenta 2: Memória (Texto) ---
@mcp.tool()
def ler_historico_pessoal() -> str:
    """Lê o diário de sonhos do usuário."""
    if not os.path.exists(DIARIO_PATH):
        return "Aviso: Diário não encontrado."
    with open(DIARIO_PATH, "r", encoding="utf-8") as f:
        return f"--- Histórico do Usuário ---\n{f.read()}"


# --- Ferramenta 3: Geração de Imagem (Manual via Requests) ---
@mcp.tool()
def gerar_imagem_do_sonho(descricao_visual: str) -> str:
    """
    Gera uma imagem usando DALL-E 3 via API REST direta.
    Args:
        descricao_visual: Prompt detalhado em inglês.
    """
    try:
        print(f"Solicitando imagem à OpenAI (POST manual): {descricao_visual}...", file=sys.stderr)
        
        # Configuração manual da requisição HTTP
        url = "https://api.openai.com/v1/images/generations"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
        data = {
            "model": "dall-e-3",
            "prompt": f"Artistic dream interpretation, surrealist style: {descricao_visual}",
            "n": 1,
            "size": "1024x1024",
            "quality": "standard"
        }

        # Forçamos o método POST aqui
        response = requests.post(url, headers=headers, json=data)
        
        # Verificação de erro
        if response.status_code != 200:
            return f"Erro na API OpenAI ({response.status_code}): {response.text}"

        # Pega a URL da imagem no JSON de resposta
        response_json = response.json()
        image_url = response_json['data'][0]['url']
        
        # Salva a imagem localmente
        img_data = requests.get(image_url).content
        nome_arquivo = "sonho_atual.png"
        caminho_absoluto = os.path.abspath(nome_arquivo)
        
        with open(nome_arquivo, 'wb') as handler:
            handler.write(img_data)
            
        print("Imagem salva com sucesso!", file=sys.stderr)
        return f"Imagem gerada e salva em: {caminho_absoluto}"
        
    except Exception as e:
        return f"Erro crítico ao gerar imagem: {e}"

if __name__ == "__main__":
    mcp.run()