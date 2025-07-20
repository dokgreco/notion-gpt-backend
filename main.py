from fastapi import FastAPI
from notion_client import Client
import openai
import os
import time

app = FastAPI()

openai.api_key = os.getenv("OPENAI_API_KEY")
notion = Client(auth=os.getenv("NOTION_API_KEY"))
assistant_id = os.getenv("GPT_AGENT_ID")

# ID corretti al 100% dei tuoi database Notion
DATABASES = {
    "Project Vertical": "20740451-33b1-80ac-aa6a-f740441d49be",
    "Case histories": "1f540451-33b1-8058-982d-f358ff5346bf",
    "Vertical Insight": "1f840451-33b1-80b9-9ce8-c3c58c303044",
    "Dataset benchmark": "18940451-33b1-8014-a2e3-fd529221b974"
}

# Funzione per estrarre automaticamente dati da un DB Notion
def get_notion_data(db_id):
    results = notion.databases.query(database_id=db_id)["results"]
    extracted = ""
    for res in results:
        title_prop = next(
            (prop for prop in res["properties"].values() if prop["type"] == "title"),
            None
        )
        if title_prop and title_prop["title"]:
            extracted += "- " + title_prop["title"][0]["text"]["content"] + "\n"
    return extracted

@app.get("/chatbot")
def chatbot(query: str):
    notion_contents = ""
    for db_name, db_id in DATABASES.items():
        notion_contents += f"\n--- {db_name} ---\n"
        notion_contents += get_notion_data(db_id)

    full_prompt = f"""
    Domanda utente: {query}

    Informazioni rilevanti dai database Notion:{notion_contents}
    """

    thread = openai.beta.threads.create()
    openai.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=full_prompt
    )

    run = openai.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )

    while run.status != 'completed':
        time.sleep(1)
        run = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

    messages = openai.beta.threads.messages.list(thread_id=thread.id)
    risposta = messages.data[0].content[0].text.value

    return {"risposta": risposta}
