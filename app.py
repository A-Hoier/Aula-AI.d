import os
from datetime import datetime
from uuid import uuid4

import dash
import dash_mantine_components as dmc
import requests
from dash import dcc, html
from dash.dependencies import Input, Output, State
from dotenv import load_dotenv
from flask import Flask
from starlette.middleware.wsgi import WSGIMiddleware

from src.constants import AVAILABLE_AGENTS, AVAILABLE_MODELS

load_dotenv()

print(os.getenv("BACKEND_URL"))


def send_query(text: str, llm: str, agent: str) -> str:
    response = requests.get(
        os.getenv("BACKEND_URL") + "chat",
        params={"query": text, "model": llm, "agent": agent},
    )
    if response.status_code != 200:
        return f"Error: {response.status_code}, {response.text}"

    return str(response.json())


app = dash.Dash(__name__, external_stylesheets=[dmc.theme])


app.layout = dmc.MantineProvider(
    theme={"colorScheme": "light"},
    children=[
        dcc.Store(id="messages-store", data=[]),
        dcc.Store(id="is-typing", data=False),
        dmc.Container(
            size="sm",
            style={
                "height": "90vh",
                "display": "flex",
                "flexDirection": "column",
                "paddingTop": "1rem",
            },
            children=[
                dmc.Card(
                    shadow="sm",
                    radius="md",
                    style={"flex": 1, "display": "flex", "flexDirection": "column"},
                    children=[
                        dmc.CardSection(
                            withBorder=True,
                            children=dmc.Group(
                                [
                                    dmc.Text("Agent", ta="center", size="xl"),
                                    dmc.Stack(
                                        [
                                            dmc.Text("select model", size="xs"),
                                            dmc.Select(
                                                value=AVAILABLE_MODELS[0],
                                                placeholder="Select model",
                                                id="llm-select",
                                                data=AVAILABLE_MODELS,
                                            ),
                                        ],
                                        gap=1,
                                    ),
                                    dmc.Stack(
                                        [
                                            dmc.Text("select agent", size="xs"),
                                            dmc.Select(
                                                value=AVAILABLE_AGENTS[1],
                                                placeholder="Select model",
                                                id="agent-select",
                                                data=AVAILABLE_AGENTS,
                                            ),
                                        ],
                                        gap=1,
                                    ),
                                ],
                                justify="space-between",
                                p="sm",
                            ),
                        ),
                        dmc.LoadingOverlay(id="loading-overlay", visible=False),
                        html.Div(
                            id="chat-container",
                            style={"flex": 1, "overflowY": "auto", "padding": "1rem"},
                        ),
                        dmc.Group(
                            pos="apart",
                            style={"margin": "1rem"},
                            children=[
                                dmc.TextInput(
                                    id="chat-input",
                                    placeholder="Type your message...",
                                    style={"flex": 1},
                                ),
                                dmc.Button(
                                    id="send-button",
                                    children="Send",
                                    variant="filled",
                                ),
                            ],
                        ),
                    ],
                )
            ],
        ),
    ],
)


@app.callback(
    [
        Output("messages-store", "data"),
        Output("chat-input", "value"),
        Output("is-typing", "data"),
    ],
    [Input("send-button", "n_clicks"), Input("chat-input", "n_submit")],
    [
        State("chat-input", "value"),
        State("messages-store", "data"),
        State("llm-select", "value"),
        State("agent-select", "value"),
    ],
    running=[
        (Output("loading-overlay", "visible", allow_duplicate=True), True, False),
    ],
    prevent_initial_call=True,
)
def update_messages(n_clicks, n_submit, text, messages, llm, agent):
    if not llm:
        return messages, "", False
    if not agent:
        return messages, "", False
    if not text:
        return messages, "", False
    user_message = {
        "id": str(uuid4()),
        "text": text,
        "is_user": True,
        "timestamp": datetime.now().strftime("%H:%M"),
    }
    messages = messages + [user_message]
    dash.callback_context.outputs_list[2]["value"] = True
    bot_response = send_query(text, llm, agent)

    bot_message = {
        "id": str(uuid4()),
        "text": bot_response,
        "is_user": False,
        "timestamp": datetime.now().strftime("%H:%M"),
    }
    messages = messages + [bot_message]

    return messages, "", False


@app.callback(
    [Output("chat-container", "children"), Output("loading-overlay", "visible")],
    [Input("messages-store", "data"), Input("is-typing", "data")],
)
def display_messages(messages, is_typing):
    children = []
    for msg in messages:
        align = "flex-end" if msg["is_user"] else "flex-start"
        bg = "#b2f5ea" if msg["is_user"] else "#edf2f7"
        fg = "#0c4a6e" if msg["is_user"] else "#1a202c"
        children.append(
            html.Div(
                style={"display": "flex", "justifyContent": align},
                children=dmc.Paper(
                    p="sm",
                    radius="md",
                    shadow="xs",
                    style={
                        "backgroundColor": bg,
                        "color": fg,
                        "maxWidth": "80%",
                        "marginBottom": "0.5rem",
                    },
                    children=[
                        dcc.Markdown(msg["text"]),
                        html.Div(
                            msg["timestamp"],
                            style={
                                "fontSize": "0.75rem",
                                "textAlign": "right",
                                "marginTop": "0.25rem",
                            },
                        ),
                    ],
                ),
            )
        )
    if is_typing:
        children.append(
            html.Div(
                style={"display": "flex", "justifyContent": "flex-start"},
                children=dmc.Loader(type="dots"),
            )
        )
    return children, is_typing


server: Flask = app.server  # type: ignore

# Create an ASGI application by wrapping the Flask app
asgi_app = WSGIMiddleware(server)


@server.route("/health")
def health():
    return "OK"


if __name__ == "__main__":
    app.run_server(debug=True, dev_tools_hot_reload=True)
