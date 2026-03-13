import os
import json
import uvicorn
from fastapi import FastAPI
from google.cloud import discoveryengine_v1 as discoveryengine
from google.oauth2 import service_account

app = FastAPI()

# --- CONFIGURAÇÕES DO GOOGLE CLOUD ---
PROJECT_ID = "toqan-standvirtual-agent" 
LOCATION = "global"
# O ID exato que retirei da sua imagem:
DATA_STORE_ID = "standvirtual-support-search_1773401932233" 

def search_knowledge(query: str):
    try:
        # 1. Carregar a chave JSON em segurança a partir do Render
        creds_json_str = os.environ.get("GOOGLE_CREDENTIALS_JSON")
        if not creds_json_str:
            return "Erro no Servidor: A chave JSON não foi encontrada nas variáveis de ambiente."
        
        creds_info = json.loads(creds_json_str)
        credentials = service_account.Credentials.from_service_account_info(creds_info)

        # 2. Ligar ao Google Cloud com essa chave
        client = discoveryengine.SearchServiceClient(credentials=credentials)
        
        # 3. Preparar a pesquisa
        serving_config = client.serving_config_path(
            project=PROJECT_ID,
            location=LOCATION,
            data_store=DATA_STORE_ID,
            serving_config="default_config"
        )

        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=query,
            page_size=3, # Traz os 3 melhores excertos do seu manual
        )

        response = client.search(request)
        
        # 4. Juntar as respostas
        context_chunks = []
        for result in response.results:
            for snippet in result.document.derived_struct_data.get("snippets", []):
                context_chunks.append(snippet.get("snippet", ""))

        if not context_chunks:
            return "Não encontrei informação sobre isso na base de dados do Standvirtual."

        return "\n\n---\n\n".join(context_chunks)

    except Exception as e:
        return f"Erro ao consultar o Google Cloud: {str(e)}"

# --- ENDPOINTS PARA O TOQAN ---
@app.get("/tools/list")
def list_tools():
    return {
        "tools": [
            {
                "name": "search_knowledge",
                "description": "Procura regras, templates e procedimentos na base de dados do Standvirtual.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"}
                    },
                    "required": ["query"]
                }
            }
        ]
    }

@app.post("/tools/call")
def call_tool(data: dict):
    tool_name = data.get("tool")

    if tool_name == "search_knowledge":
        query = data["arguments"]["query"]
        result = search_knowledge(query)
        return {"result": result}
    else:
        return {"error": "Tool not found"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)