import os
import json
import uvicorn
from fastapi import FastAPI, Request
from mcp.server.fastmcp import FastMCP
from google.cloud import discoveryengine_v1 as discoveryengine
from google.oauth2 import service_account
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

# 1. Configurar o MCP
mcp = FastMCP("Standvirtual")

PROJECT_ID = "toqan-standvirtual-agent" 
DATA_STORE_ID = "standvirtual-support-search_1773401932233" 

@mcp.tool()
def search_knowledge(query: str) -> str:
    """Procura regras e templates no manual do Standvirtual."""
    try:
        creds_json_str = os.environ.get("GOOGLE_CREDENTIALS_JSON")
        creds_info = json.loads(creds_json_str)
        credentials = service_account.Credentials.from_service_account_info(creds_info)
        client = discoveryengine.SearchServiceClient(credentials=credentials)
        
        serving_config = client.serving_config_path(
            project=PROJECT_ID, location="global", data_store=DATA_STORE_ID, serving_config="default_config"
        )

        response = client.search(discoveryengine.SearchRequest(
            serving_config=serving_config, query=query, page_size=3
        ))
        
        results = []
        for res in response.results:
            for s in res.document.derived_struct_data.get("snippets", []):
                results.append(s.get("snippet", ""))

        return "\n\n---\n\n".join(results) if results else "Sem resultados."
    except Exception as e:
        return f"Erro: {str(e)}"

# 2. Criar a App FastAPI
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# RESOLVE O ERRO DO /SSE (Maiúsculas)
@app.get("/SSE")
async def redirect_sse_upper():
    return RedirectResponse(url="/sse")

# RESOLVE O ERRO DO POST / (404)
@app.api_route("/", methods=["GET", "POST", "OPTIONS"])
async def home_permissive(request: Request):
    return {"status": "MCP Server is Running", "info": "Use /sse for connection"}

# Montar o MCP
mcp_app = mcp.streamable_http_app()
app.mount("/", mcp_app)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
