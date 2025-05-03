from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from src.agent import get_response

# Set up FastAPI app
app = FastAPI()
# Allow CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def root():
    """
    html code with a welcome, and a link to docs"""
    return """
    <html>
        <head>
            <title>Welcome to the FastAPI app</title>
        </head>
        <body>
            <h1>Welcome to the FastAPI app</h1>
            <p><a href="/docs">Go to docs</a></p>
        </body>
    </html>
    """


@app.get("/chat")
async def chat(query: str, model: str = "gpt-4o", agent: str = "research_agent"):
    """
    Chat endpoint
    """
    return await get_response(query, model, agent)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
