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
from datetime import datetime
from typing import Optional, List
import uuid

load_dotenv()


class Task(BaseModel):
    id: str
    title: str
    completed: bool = False
    created_at: datetime = datetime.now()
    due_date: Optional[str] = None
    due_time: Optional[str] = None


tasks: List[Task] = []

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


@tool
def add_task(title: str, due_date: Optional[str] = None, due_time: Optional[str] = None):
    """adds task to tasks list
    Args:
    title : task description (Ex: Buy groceries)
    due_date: optional date like today or tomorrow , or "2026-02-21"
    due_time: optional like "18:00" or "6PM"
    """

    task_id = str(uuid.uuid4())[:8]
    new_task = Task(
        id=task_id,
        title=title,
        due_date=due_date,
        due_time=due_time,
        completed=False,
        created_at=datetime.now().isoformat()

    )
    tasks.append(new_task)
    return f"added task {title} with id {task_id} "


@tool
def list_tasks(day: Optional[str] = None):
    """
    Provides list of tasks for given day
    args:
     day: "today", "tomorrow" or date like 2026-2-21. If None provided shows all tasks
    """

    filtered_tasks = []
    if day is None:
        filtered_tasks = tasks
    else:
        for task in tasks:
            if task.due_date == day:
                filtered_tasks.append(task)
    return filtered_tasks


llm = ChatGroq(model="openai/gpt-oss-120b")

tools = [add_task, list_tasks]

agent = agents.create_agent(
    llm,
    tools,

    system_prompt="""You are a helpful task management assistant . Help users to add their task and
    review their tasks list.Always be concise and friendly
""",
    checkpointer=InMemorySaver(),

)

__all__ = ["agent"]

if __name__ == "__main__":
    result= agent.invoke(
        {"messages": [{"role": "user", "content": "Call Mom tomorrow"}]},
        {"configurable": {"thread_id": "1"}}
    )
    print("response",result["messages"][-1].content)
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "go to gym 6pm today"}]},
        {"configurable": {"thread_id": "1"}}
    )
    print("response", result["messages"][-1].content)
    result= agent.invoke(
        {"messages":[{"role":"user", "content":"show me today's tasks"}]},
        {"configurable": {"thread_id": "1"}}
    )
    print("response", result["messages"][-1].content)