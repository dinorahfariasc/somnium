import asyncio
from mcp.client.stdio import StdioServerParameters
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client

async def run():
    # Configura a conexão com seu servidor
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"], 
    )

    print("🔌 Conectando ao servidor MCP...")

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 1. Inicializa
            await session.initialize()
            
            # 2. Lista ferramentas disponíveis (Deve aparecer 'gerar_imagem_do_sonho')
            tools = await session.list_tools()
            print(f"\n--- Ferramentas Disponíveis: {len(tools.tools)} ---")
            for t in tools.tools:
                print(f"- {t.name}: {t.description[:50]}...")

            # 3. Testa Leitura de Diário
            print("\n--- Testando: Ler Diário ---")
            resultado_diario = await session.call_tool("ler_historico_pessoal")
            print(resultado_diario.content[0].text[:100] + "...") # Mostra só o começo

            # 4. Testa RAG
            print("\n--- Testando: Consultar Significado (Cobra) ---")
            resultado_rag = await session.call_tool(
                "consultar_significado_onirico", 
                arguments={"relato_sonho": "cobra verde picando"}
            )
            print("RAG retornou resultados.")

            # 5. TESTE DE IMAGEM (NOVO) 🎨
            print("\n--- Testando: Geração de Imagem (Isso pode demorar!) ---")
            print("⚠️  Aguarde... baixando modelo ou carregando na GPU...")
            
            # Nota: Stable Diffusion entende melhor inglês, por isso o prompt em inglês
            resultado_img = await session.call_tool(
                "gerar_imagem_do_sonho", 
                arguments={"descricao_visual": "surrealist painting of a green snake in a dark forest, highly detailed, 8k"}
            )
            print(f"RESPOSTA DO SERVIDOR: {resultado_img.content[0].text}")

if __name__ == "__main__":
    asyncio.run(run())