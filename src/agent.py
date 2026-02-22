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


@tool
def complete_task(task_id: str) -> str:
    """
    Mark a task completed using its ID

      Args:
        task_id: The task ID (e.g., 'abc12345')

    """
    for task in tasks:
        if task.id == task_id:
            task.completed = True
            return f"{task.title} completed"
    return f"{task_id} task id not found"


@tool
def edit_task(task_id: str, updated_title: str, updated_due_date: Optional[str] = None,
              updated_due_time: Optional[str] = None) -> str:
    """
    Edit task by task id
    Args:
        task_id : The task ID (e.g., 'abc12345')
        updated_title: new/updated title of task
        updated_due_time: new/updated due time, its Optional arg
        updated_due_date: new/updated due date, its Optional args
    """

    for task in tasks:
        if task.id == task_id:
            task.title = updated_title
            if updated_due_date is not None:
                task.due_date = updated_due_date
            if updated_due_time is not None:
                task.due_time = updated_due_time
            return f"{task_id} updated with title  {updated_title}, due date {updated_due_date}, due time {updated_due_time} "
        return "f{task_id} not found"


@tool
def delete_task(task_id: str) -> str:
    """
    Deletes task by id

    args:
    task_id: The task ID (e.g., 'abc12345')
    """
    for task in tasks:
        if task.id == task_id:
            tasks.remove(task)
        return f"{task_id} deleted"
    return f"{task_id} not found"


llm = ChatGroq(model="openai/gpt-oss-120b")

tools = [add_task, list_tasks, complete_task, edit_task, delete_task]

agent = agents.create_agent(
    llm,
    tools,

    system_prompt="""You are a helpful task management assistant . Help users to add their task and
    review their tasks list.
    
    IMPORTANT: When users want to complete,edit or delete a task:
1. First call list_tasks() to see all tasks with their IDs
2. Find the matching task by title
3. Use the task ID to complete/edit/delete it

Example:
User: "Complete gym"
You: *call list_tasks()* → see [abc123] Gym @ 6pm
You: *call complete_task("abc123")*
You: "✅ Done! Marked gym as complete."
    
    Always be concise and friendly
""",
    checkpointer=InMemorySaver(),

)

__all__ = ["agent"]

if __name__ == "__main__":
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "Call Mom tomorrow"}]},
        {"configurable": {"thread_id": "1"}}
    )
    print("response", result["messages"][-1].content)
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "go to gym 6pm today"}]},
        {"configurable": {"thread_id": "1"}}
    )
    print("response", result["messages"][-1].content)
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "show me today's tasks"}]},
        {"configurable": {"thread_id": "1"}}
    )
    print("response", result["messages"][-1].content)
