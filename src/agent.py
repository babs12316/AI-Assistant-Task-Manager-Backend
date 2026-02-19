from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain import agents
from langchain.agents.middleware import before_agent, AgentState, before_model
from langgraph.runtime import Runtime
from langchain.messages import AIMessage
import httpx
from pydantic import BaseModel, Field
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

WEATHER_KEYWORDS = [
    'weather', 'temperature', 'rain', 'snow', 'sunny', 'cloudy',
    'forecast', 'climate', 'humidity', 'wind', 'storm', 'thunder',
    'cold', 'hot', 'warm', 'cool', 'precipitation', 'degrees',
    'celsius', 'fahrenheit', 'overcast', 'drizzle', 'hail'
]


class CustomAgentState(AgentState):
    preferences: dict = {}


class WeatherReport(BaseModel):
    city: str
    temperature: float = Field(..., description="temp in Celsius (e.g. 22.5)")
    windspeed: float = Field(..., description="Wind speed km/h (e.g. 12.3)")
    city: str = Field(..., description="City name")


@before_model()
def get_user_preferences(state: CustomAgentState, runtime: Runtime):
    msg = state["messages"][-1].content
    if "fahrenheit" in msg:
        state["preferences"]["temperature"] = "fahrenheit"
    else:
        state["preferences"]["temperature"] = "degree celsius"


@before_agent(can_jump_to=["end"])
def is_weather_related_query(state: CustomAgentState, runtime: Runtime):
    print("hey State message", state["messages"][-1].content)
    is_weather_related = any(keyword in state["messages"][-1].content for keyword in WEATHER_KEYWORDS)
    if is_weather_related is False:
        return {
            "messages": [AIMessage("I can only answer weather-related queries")],
            "goto": "end"
        }

    return None


@tool
def get_weather(city: str) -> WeatherReport | str:
    """
    Get current weather for ANY city worldwide using Open-Meteo (free API).

    Provides:
    • Temperature (°C)
    • Wind speed (km/h)

    INPUT: City name only (e.g., "London", "New York", "Tokyo")
    OUTPUT: Current conditions summary

    Handles: 10,000+ cities, auto-geocoding, error handling.
    """
    try:
        # 1️⃣ Geocode city → lat/lon
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_params = {
            "name": city,
            "count": 1,
            "language": "en",
            "format": "json"
        }

        with httpx.Client(timeout=10) as client:
            geo_resp = client.get(geo_url, params=geo_params)
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()

        if "results" not in geo_data:
            return f"Sorry, I couldn't find weather data for {city}."

        location = geo_data["results"][0]
        lat = location["latitude"]
        lon = location["longitude"]

        # 2️⃣ Get current weather
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": True
        }

        with httpx.Client(timeout=10) as client:
            weather_resp = client.get(weather_url, params=weather_params)
            weather_resp.raise_for_status()
            weather_data = weather_resp.json()

        current = weather_data["current_weather"]

        temperature = current["temperature"]
        windspeed = current["windspeed"]

        return WeatherReport(temperature=temperature, windspeed=windspeed, city=city)

    except Exception as e:
        return f"Failed to fetch weather for {city}: {str(e)}"


llm = ChatGroq(model="openai/gpt-oss-120b")

tools = [get_weather]

agent = agents.create_agent(
    llm,
    tools,
    middleware=[is_weather_related_query],
    system_prompt="""You are a weather assistant that handles all weather-related questions.
    To create a line break or new line (`<br>`), end a line with two or more spaces, and then type return.
""",
    checkpointer=InMemorySaver(),
    state_schema=CustomAgentState
)

__all__ = ["agent"]

if __name__ == "__main__":
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "How is weather in Frankfurt?."}]},
        {"configurable": {"thread_id": "1"}},
    )
    print("✅ Weather result:", result)

    for chunk in agent.stream(
            {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
            {"configurable": {"thread_id": "1"}},
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
