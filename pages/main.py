import asyncio
import os

import dash
import dash_bootstrap_components as dbc
import requests
from lib.components.chat_components import (
    render_bubbles,
    render_chat_container,
    render_input_box,
)
from dash import Input, Output, State, callback, html, dcc, ctx
from dash.exceptions import PreventUpdate
from dotenv import load_dotenv

from lib.models import AIResponse, Conversation, Message, MsgPair
from lib.api_service import llm_service

load_dotenv()
WELCOME_MSG = "WELCOME_MSG"
dash.register_page(__name__, path="/")


def layout():
    """The chatbot layout."""
    return html.Div(
        [
            render_chat_container(),
            render_input_box(),
            dcc.Store(id="pending-message-store", data=None),
            html.Div(id="scroll-output", style={"display": "none"}),
        ]
    )


@callback(
    Output("conversation-store", "data"),
    Output("pending-message-store", "data"),
    Output("user-input", "value", allow_duplicate=True),
    Output("user-input", "disabled", allow_duplicate=True),
    Input("user-input", "n_submit"),
    Input("send-btn", "n_clicks"),
    State("conversation-store", "data"),
    State("user-input", "value"),
    prevent_initial_call=True,
)
def add_user_message(n_submit, n_clicks, conversation_data: Conversation, user_input):
    """Immediately adds the user message to the conversation."""
    if not n_submit and not n_clicks:
        raise PreventUpdate
    if not user_input:
        raise PreventUpdate

    conversation = Conversation(**conversation_data)

    # Append user input to the conversation
    user_message = Message(message=user_input)

    # Create a temporary response with loading indicator
    loading_response = AIResponse(response="", is_loading=True)

    # Append user message with temporary loading response
    conversation.messages.append(
        MsgPair(message=user_message, response=loading_response)
    )

    # Store the user input for the next callback to process
    return conversation.model_dump(), user_input, "", True


@callback(
    Output("user-input", "value"),
    Output("send-btn", "disabled"),
    Output("conversation-store", "data", allow_duplicate=True),
    Input("pending-message-store", "data"),
    State("conversation-store", "data"),
    prevent_initial_call=True,
)
def process_ai_response(user_input, conversation_data):
    """Process the AI response asynchronously after user message is displayed."""
    if not user_input:
        raise PreventUpdate

    conversation = Conversation(**conversation_data)

    # Call the API for a response
    try:
        bot_reply = llm_service.chat(user_input)
        if not bot_reply:
            bot_reply = "Sorry, there was an issue connecting to the chat service."
    except requests.RequestException:
        bot_reply = "Sorry, there was an issue connecting to the chat service."

    # Update the last message's response
    conversation.messages[-1].response = AIResponse(
        response=bot_reply, is_loading=False
    )

    return "", False, conversation.model_dump()


@callback(
    Output("chat-window", "children"),
    Output("user-input", "disabled", allow_duplicate=True),
    Input("conversation-store", "data"),
    prevent_initial_call=True,
)
def update_chat_window(conversation_data):
    """Updates the chat window when the conversation changes."""
    if not conversation_data:
        raise PreventUpdate

    conversation = Conversation(**conversation_data)
    return render_bubbles(conversation), False
