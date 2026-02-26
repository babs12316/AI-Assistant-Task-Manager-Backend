# AI Assistant Task Manager (Backend)

A **FastAPI-powered backend** with **LangChain AI agents** for intelligent task management.  
Built with **LangGraph**, **Groq LLM**, and **streaming responses** via Server-Sent Events (SSE).

**Frontend Repository:** [AI-Assistant-Task-Manager-Frontend](https://github.com/babs12316/AI-Assistant-Task-Manager-Frontend)

---

## 🚀 Features

- 🤖 **AI-powered task management** using LangChain agents
- 🛠️ **5 core tools**: Add, List, Complete, Edit, Delete tasks
- ⚡ **Real-time streaming** responses via SSE
- 🧵 **Thread-based memory** for conversation context
- 🎯 **Multi-agent architecture** with tool orchestration
- 📝 **Natural language processing** - users interact conversationally
- 🔄 **FastAPI** for high-performance async endpoints

---

## 📦 Installation

### Prerequisites

- **Python 3.9+**
- **uv** package manager ([Install uv](https://docs.astral.sh/uv/getting-started/installation/))
- **Groq API Key** ([Get one here](https://console.groq.com/keys))

### Install uv
```bash
# macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Setup
```bash
# Clone repository
git clone https://github.com/babs12316/AI-Assistant-Task-Manager-Backend.git
cd AI-Assistant-Task-Manager-Backend

# Install dependencies
uv sync

# Create .env file
echo "GROQ_API_KEY=your_groq_api_key_here" > .env
```

### Get Your Groq API Key

1. Visit [Groq Console](https://console.groq.com/keys)
2. Sign up or log in
3. Generate a new API key
4. Add it to your `.env` file

---

## 🎯 Usage

### Start the Server
```bash
uv run uvicorn src.api:app --reload
```

Server will run at: **http://localhost:8000**

### Health Check
```bash
curl http://localhost:8000/health
```

Response:
```json
{"status": "healthy"}
```

---

## 📡 API Endpoints

### `POST /chat`

Stream AI agent responses using Server-Sent Events.

**Request:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Add gym at 6pm today",
    "thread_id": "user-123"
  }'
```

**Response (SSE Stream):**
```
data: ✅ Added **Gym** [9a8cca01] for today at **6 PM**.  
data: 
data: Anything else you'd like to add?  
data: [DONE]
```

**Request Body:**
```json
{
  "message": "string",    // User's natural language input (required)
  "thread_id": "string"   // Unique conversation thread ID (required)
}
```

**Thread ID:**
- Use the same `thread_id` to maintain conversation context
- Each user should have a unique thread ID
- Example: `"user-123"`, `"session-abc-456"`, etc.

---

## 🛠️ Available Tools

The AI agent has access to these tools:

### 1. **add_task**
Add a new task to the list.

**Example:**
- User: `"Add gym at 6pm today"`
- Agent: `add_task("Gym", "today", "18:00")`
- Response: `"✅ Added 'Gym' [abc123] for today at 6 PM"`

### 2. **list_tasks**
List tasks for a specific day or all tasks.

**Example:**
- User: `"Show me today's tasks"`
- Agent: `list_tasks("today")`
- Response: Task list with IDs

### 3. **complete_task**
Mark a task as completed.

**Example:**
- User: `"Complete gym"`
- Agent: Finds task ID → `complete_task("abc123")`
- Response: `"🎉 Awesome! Marked 'Gym' as complete!"`

### 4. **edit_task**
Edit an existing task.

**Example:**
- User: `"Change gym to 7pm"`
- Agent: `edit_task("abc123", updated_due_time="19:00")`
- Response: `"✅ Updated 'Gym': time → 19:00"`

### 5. **delete_task**
Delete a task.

**Example:**
- User: `"Delete gym"`
- Agent: `delete_task("abc123")`
- Response: `"🗑️ Deleted: Gym"`

---

## 🧠 How the AI Agent Works

### Agent Workflow
```
User: "Add gym at 6pm and show my tasks"
    ↓
Agent analyzes intent
    ↓
Step 1: Calls add_task("Gym", "today", "18:00")
    ↓
Step 2: Calls list_tasks("today")
    ↓
Streams response back to user via SSE
    ↓
User sees: "✅ Added Gym. 📋 Tasks: [abc123] Gym @ 6 PM"
```

### Multi-Step Reasoning Example
```
User: "Complete gym"
  ↓
Agent: "I need to find the gym task ID first"
  ↓
Agent: Calls list_tasks() → Finds [abc123] Gym
  ↓
Agent: Calls complete_task("abc123")
  ↓
Agent: "✅ Nice work! 'Gym' is done!"
```

---

## 📝 Example Interactions

| User Input                         | Agent Actions                              |
| ---------------------------------- | ------------------------------------------ |
| `Add gym at 6pm`                   | `add_task("Gym", "today", "18:00")`        |
| `Show my tasks`                    | `list_tasks()`                             |
| `What's on my plate today?`        | `list_tasks("today")`                      |
| `Complete gym`                     | `list_tasks()` → `complete_task("abc123")` |
| `Change lunch to 2pm`              | `list_tasks()` → `edit_task(...)`          |
| `Delete the gym task`              | `list_tasks()` → `delete_task("abc123")`   |
| `Add gym and call mom, then list`  | Multiple tool calls in sequence            |

---

## 📋 Response Examples

### Adding a Task
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Add gym at 6pm", "thread_id": "user-123"}'
```

**Response:**
```
data: ✅ Added **Gym** [9a8cca01] for today at **6 PM**.
data: 
data: Anything else you'd like to add?
data: [DONE]
```

### Listing Tasks
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show my tasks", "thread_id": "user-123"}'
```

**Response:**
```
data: 📋 Tasks (2):
data: 
data: [9a8cca01] ○ Gym @ 6 PM
data: [f3b2c456] ○ Call Mom @ 3 PM
data: 
data: You have 2 tasks pending.
data: [DONE]
```

### Completing a Task
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Complete gym", "thread_id": "user-123"}'
```

**Response:**
```
data: 🎉 Awesome! Marked 'Gym' as complete!
data: [DONE]
```

---

## 🏗️ Project Structure
```
AI-Assistant-Task-Manager-Backend/
├── src/
│   ├── agent.py          # LangChain agent + tools
│   ├── api.py            # FastAPI routes
│   └── api/
│       └── health.py     # Health check endpoint
├── tests/
│   └── test_agent.py     # Unit tests
├── .env                  # Environment variables (create this)
├── pyproject.toml        # Project dependencies
├── uv.lock              # Locked dependencies
└── README.md             # This file
```

---

## 📚 Tech Stack

- **FastAPI** - Modern, fast web framework
- **LangChain** - AI agent orchestration framework
- **LangGraph** - Agent workflow management
- **Groq** - Ultra-fast LLM inference (model: `openai/gpt-oss-120b`)
- **Pydantic** - Data validation
- **Server-Sent Events (SSE)** - Real-time streaming
- **uvicorn** - ASGI server
- **uv** - Fast Python package manager

---

## 🔧 Configuration

### CORS Settings

Edit `src/api.py` to add allowed origins:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",           # Vite dev server
        "https://tasky22.vercel.app",      # Production frontend
        "https://your-domain.com"          # Your domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Change LLM Model

Edit `src/agent.py`:
```python
# Current model
llm = ChatGroq(model="openai/gpt-oss-120b")

# Other Groq models
llm = ChatGroq(model="llama-3.1-70b-versatile")
llm = ChatGroq(model="mixtral-8x7b-32768")
```

---

## 📖 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🔗 Related Repositories

- **Frontend Repository**: [AI-Assistant-Task-Manager-Frontend](https://github.com/babs12316/AI-Assistant-Task-Manager-Frontend)

---

**⭐ If you like this project, give it a star on GitHub!**