from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from src.api.health import router as health_router

load_dotenv()

app = FastAPI()

app.include_router(health_router)

WEATHER_KEYWORDS = [
    'weather', 'temperature', 'rain', 'snow', 'sunny', 'cloudy',
    'forecast', 'climate', 'humidity', 'wind', 'storm', 'thunder',
    'cold', 'hot', 'warm', 'cool', 'precipitation', 'degrees',
    'celsius', 'fahrenheit', 'overcast', 'drizzle', 'hail'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://first-agent-ui.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatInput(BaseModel):
    message: str
    thread_id: str


def stream_response(message: str, thread_id: str):
    """Generator function that yields SSE chunks"""
    from src.agent import agent
    for chunk in agent.stream(
            {"messages": [{"role": "user", "content": message}]},
            {"configurable": {"thread_id": thread_id}},
            stream_mode="updates",
    ):
        for step, data in chunk.items():
            print(f"step: {step}")

            if step == "model":
                blocks = data["messages"][-1].content_blocks
                print(f"blocks are {blocks}")
                for block in blocks:
                    if block.get("type") == "text":
                        print("TEXT:", block["text"])
                        text = block["text"]
                        for line in text.split("\n"):
                            yield f"data: {line}\n"
                        yield "\n"


@app.post("/chat")
def chat(request: ChatInput):
    return StreamingResponse(
        stream_response(request.message, request.thread_id),  # Pass the generator
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
