from fastapi import FastAPI
from notion_client import Client
import openai
import os
import time

app = FastAPI()

openai.api_key = os.getenv("OPENAI_API_KEY")
notion = Client(auth=os.getenv("NOTION_API_KEY"))
assistant_id = os.getenv("GPT_AGENT_ID")

@app.get("/chatbot")
def chatbot(query: str):

    db_id = "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"

    notion_data = notion.databases.query(database_id=db_id)
    
    extracted_info = ""
    for result in notion_data["results"]:
        title = result["properties"]["Name"]["title"]
        if title:
            extracted_info += title[0]["text"]["content"] + "\n"
    
    thread = openai.beta.threads.create()

    openai.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=f"Domanda utente: {query}\n\nDati da Notion:\n{extracted_info}"
    )

    run = openai.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )

    while run.status != 'completed':
        time.sleep(1)
        run = openai.beta.threads.runs.retrieve(
            thread_id=thread.id, run_id=run.id
        )

    messages = openai.beta.threads.messages.list(thread_id=thread.id)
    risposta = messages.data[0].content[0].text.value

    return {"risposta": risposta}
