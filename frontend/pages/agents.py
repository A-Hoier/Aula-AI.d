from dash import html, Input, Output, State, callback, dcc
import dash
import dash_bootstrap_components as dbc
from lib.api_service import api_service

dash.register_page(__name__, path="/agents")


def layout():
    return html.Div(
        [
            dbc.Container(
                [
                    dbc.Row(
                        dbc.Col(
                            [
                                html.H1("Page not completed", className="text-center"),
                            ],
                            className="text-center",
                        ),
                        className="py-5",
                    ),
                ]
            ),
        ]
    )
