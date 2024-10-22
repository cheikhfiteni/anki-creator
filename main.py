from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv
import json
import anthropic

load_dotenv(override=True)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANKI_CONNECT_URL = "http://localhost:8765"

anthropic_client = anthropic.Client(api_key=ANTHROPIC_API_KEY)
print("API Key:", ANTHROPIC_API_KEY[:7] + "..." if ANTHROPIC_API_KEY else "None")

class Card(BaseModel):
    front: str
    back: str


class AddCardsRequest(BaseModel):
    deck_name: str
    cards: list[Card]

SYSTEM_PROMPT = """You are an AI assistant designed to create Anki flashcards based on user-provided topics. Your task is to generate a variable number of high-quality flashcards (between 3 and 7) that cover key concepts, definitions, or important facts related to the given topic. Each flashcard should have a clear front (question or prompt) and back (answer or explanation).

Output the flashcards in the following JSON format:
[
    {
        "front": "Question or prompt",
        "back": "Answer or explanation"
    },
    ...
]

Ensure that the content is accurate, concise, and educational. Avoid creating cards that are too similar or redundant."""

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/decks")
async def get_decks():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            ANKI_CONNECT_URL,
            json={
                "action": "deckNames",
                "version": 6
            }
        )
    decks = response.json()["result"]
    return {"decks": decks}

@app.get("/cards/{deck_name}")
async def get_cards(deck_name: str):
    print("deck_name", deck_name)
    async with httpx.AsyncClient() as client:
        response = await client.post(
            ANKI_CONNECT_URL,
            json={
                "action": "findCards",
                "version": 6,
                "params": {
                    "query": f"deck:\"{deck_name}\""
                }
            }
        )
        card_ids = response.json()["result"]

        if card_ids:
            response = await client.post(
                ANKI_CONNECT_URL,
                json={
                    "action": "cardsInfo",
                    "version": 6,
                    "params": {
                        "cards": card_ids
                    }
                }
            )
            cards_info = response.json()["result"]
            cards = [{"front": card["fields"]["Front"]["value"], "back": card["fields"]["Back"]["value"]} for card in cards_info]
        else:
            cards = []

    return {"cards": cards}

@app.post("/generate_cards")
async def generate_cards(topic: str = Form(...), deck_name: str = Form(...)):
    message = anthropic_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"Create Anki flashcards for the topic: {topic}. These cards will be added to the '{deck_name}' deck."}
        ]
    )
    response_data = message.content
    cards = json.loads(response_data[0].text)
    return {"cards": cards}

@app.post("/add_cards")
async def add_cards(request: AddCardsRequest):
    notes = []
    for card in request.cards:
        note = {
            "deckName": request.deck_name,
            "modelName": "Basic",
            "fields": {
                "Front": card.front,
                "Back": card.back
            },
            "options": {
                "allowDuplicate": False
            },
            "tags": ["generated"]
        }
        notes.append(note)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            ANKI_CONNECT_URL,
            json={
                "action": "addNotes",
                "version": 6,
                "params": {
                    "notes": notes
                }
            }
        )
    
    result = response.json()
    return {"result": result}
