import os
import json
from mcp.server.fastmcp import FastMCP
from google.cloud import discoveryengine_v1 as discoveryengine
from google.oauth2 import service_account
from fastapi.middleware.cors import CORSMiddleware

# Cria o servidor usando o Protocolo Oficial MCP
mcp = FastMCP("Standvirtual MCP")

# Configurações da sua base de dados
PROJECT_ID = "toqan-standvirtual-agent" 
LOCATION = "global"
DATA_STORE_ID = "standvirtual-support-search_1773401932233" 

@mcp.tool()
def search_knowledge(query: str) -> str:
    """Procura regras, templates e procedimentos na base de dados do Standvirtual."""
    try:
        creds_json_str = os.environ.get("GOOGLE_CREDENTIALS_JSON")
        if not creds_json_str:
            return "Erro: A chave JSON não foi encontrada nas variáveis de ambiente."
        
        creds_info = json.loads(creds_json_str)
        credentials = service_account.Credentials.from_service_account_info(creds_info)

        client = discoveryengine.SearchServiceClient(credentials=credentials)
        
        serving_config = client.serving_config_path(
            project=PROJECT_ID,
            location=LOCATION,
            data_store=DATA_STORE_ID,
            serving_config="default_config"
        )

        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=query,
            page_size=3,
        )

        response = client.search(request)
        
        context_chunks = []
        for result in response.results:
            for snippet in result.document.derived_struct_data.get("snippets", []):
                context_chunks.append(snippet.get("snippet", ""))

        if not context_chunks:
            return "Não encontrei informação sobre isso na base de dados do Standvirtual."

        return "\n\n---\n\n".join(context_chunks)

    except Exception as e:
        return f"Erro ao consultar o Google Cloud: {str(e)}"

# Cria a App e adiciona o Passe Livre (CORS) para o TOQAN não ser bloqueado
app = mcp.streamable_http_app()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
