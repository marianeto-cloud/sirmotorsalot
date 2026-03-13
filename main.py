import os
import json
import uvicorn
from fastapi import FastAPI, Request
from google.cloud import discoveryengine_v1 as discoveryengine
from google.oauth2 import service_account

app = FastAPI()

PROJECT_ID = "toqan-standvirtual-agent" 
DATA_STORE_ID = "standvirtual-support-search_1773401932233" 

@app.post("/search")
async def search(request: Request):
    data = await request.json()
    query = data.get("query", "")
    
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

        return {"result": "\n\n---\n\n".join(results) if results else "Sem resultados."}
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
def health():
    return {"status": "online"}
