from lib.models import ChatInput
import uvicorn

from fastapi import FastAPI, File, Form, Response, UploadFile, HTTPException, status

from lib.agent import get_response

app = FastAPI()


@app.get("/chat/")  # type: ignore
async def chat(data: ChatInput):
    """Input: user input, output: AI response."""
    return {"response": await get_response(data.user_input)}


if __name__ == "__main__":
    uvicorn.run(app)  # , host="0.0.0.0", port=8000, timeout_keep_alive=900)
