import dash
import dash_bootstrap_components as dbc

app = dash.Dash(external_stylesheets=[dbc.themes.DARKLY],
                external_scripts=[{
                    'src': 'https://kit.fontawesome.com/4ba3c16c07.js',
                    'crossorigin': 'anonymous'
                }],
                suppress_callback_exceptions=True,
                title='Utonium')
server = app.server
