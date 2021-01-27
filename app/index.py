import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

from app import app
from apps import stock_viewer, crypto_viewer
from apps import crypto_rebalancer


server = app.server
CONTENT_STYLE = {
    "marginLeft": "1rem",
    "marginRight": "1rem",
    "padding": "2rem 1rem",
}

navbar = dbc.Navbar([
    dbc.Col(dbc.NavbarBrand('Utonium', href='/'),
            sm=3, md=2, lg=1),
    dbc.Col(
        dbc.Nav([
            dbc.NavItem(dbc.NavLink("Stock Viewer",
                                    href="/apps/stock_viewer"))
        ], navbar=True),
        sm=3, md=2, lg=1
    ),
    dbc.Col(
        dbc.Nav([
            dbc.NavItem(dbc.NavLink("Crypto Viewer",
                                    href="/apps/crypto_viewer"))
        ], navbar=True),
        sm=3, md=2, lg=1
    ),
    dbc.Col(
        dbc.Nav([
            dbc.NavItem(dbc.NavLink("C-Rebalancer",
                                    href="/apps/crypto_rebalancer"))
        ], navbar=True),
        sm=3, md=2, lg=1
    ),
    # dbc.Col(
    #     dbc.Nav([
    #         dbc.NavItem(dbc.NavLink("Test",
    #                                 href="/apps/test"))
    #     ], navbar=True),
    #     sm=3, md=2, lg=1
    # ),
], color="dark", dark=True)


content = html.Div(id="page-content", style=CONTENT_STYLE)

app.layout = html.Div([dcc.Location(id="url"), navbar, content])

@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    if pathname in ['/', '/apps/stock_viewer']:
        return stock_viewer.layout
    elif pathname == '/apps/crypto_viewer':
        return crypto_viewer.layout
    elif pathname == '/apps/crypto_rebalancer':
        return crypto_rebalancer.layout
    # elif pathname == '/apps/test':
    #     return test.layout
    else:
        return dbc.Jumbotron(
            [
                html.H1("404: Not found", className="text-danger"),
                html.Hr(),
                html.P(f"The pathname {pathname} was not recognised..."),
            ]
        )


if __name__ == '__main__':
    app.run_server(debug=True)
