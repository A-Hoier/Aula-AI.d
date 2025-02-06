import os

import dash
import dash_bootstrap_components as dbc
import requests
from lib.components.chat_components import (
    render_bubbles,
    render_chat_container,
    render_input_box,
)
from dash import Input, Output, State, callback, html, dcc
from dash.exceptions import PreventUpdate
from dotenv import load_dotenv

from lib.models import AIResponse, Conversation, Message, MsgPair
from lib.api_service import api_service

load_dotenv()
WELCOME_MSG = "WELCOME_MSG"
dash.register_page(__name__, path="/")


def layout():
    """The chatbot layout."""
    return html.Div(
        [
            render_chat_container(),
            render_input_box(),
            html.Div(id="scroll-output", style={"display": "none"}),
        ]
    )


@callback(
    Output("conversation-store", "data"),
    Output("user-input", "value"),
    Output("send-btn", "disabled"),
    Input("user-input", "n_submit"),
    Input("send-btn", "n_clicks"),
    State("conversation-store", "data"),
    State("user-input", "value"),
    prevent_initial_call=True,
)
def update_conversation(
    n_submit, n_clicks, conversation_data: Conversation, user_input
):
    """Handles user input, sends it to the API, and updates the conversation."""
    if not n_submit and not n_clicks:
        raise PreventUpdate
    if not user_input:
        raise PreventUpdate

    conversation = Conversation(**conversation_data)

    # Append user input to the conversation
    user_message = Message(message=user_input)

    # Call the API for a response
    try:
        response = api_service.get_response(user_input)
        if not response:
            bot_reply = "Sorry, there was an issue connecting to the chat service."
        else:
            bot_reply = response.get("response", "Error processing the request.")
    except requests.RequestException:
        bot_reply = "Sorry, there was an issue connecting to the chat service."

    ai_response = AIResponse(response=bot_reply)

    # Append the new message pair
    conversation.messages.append(MsgPair(message=user_message, response=ai_response))

    return conversation.model_dump(), "", False


@callback(
    Output("chat-window", "children"),
    Input("conversation-store", "data"),
)
def update_chat_window(conversation_data):
    """Updates the chat window when the conversation changes."""
    conversation = Conversation(**conversation_data)
    return render_bubbles(conversation)


# @callback(
#     Output("scroll-output", "children"),
#     Input("conversation-store", "data"),
#     Input("chat-window", "children"),
# )
# def scroll_to_bottom(conversation_data, chat_content):
#     if not conversation_data:
#         raise PreventUpdate

#     return dcc.Location(id="url-scroll", href="#bottom", refresh=False)


# app.clientside_callback(
#     """
#     function(data) {
#         const chatWindow = document.getElementById('chat-window');
#         if (chatWindow) {
#             chatWindow.scrollTop = chatWindow.scrollHeight;
#         }
#         // We don't need to return anything meaningful;
#         // just return null or an empty string.
#         return '';
#     }
#     """,
#     Output("scroll-output", "children"),  # Output placeholder
#     Input("conversation-store", "data"),  # Triggers on conversation changes
# )
