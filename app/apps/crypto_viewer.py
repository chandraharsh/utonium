import dash_html_components as html
import dash_core_components as dcc
import dash_trich_components as dtc
from dash.dependencies import Input, Output, State
from dash_dangerously_set_inner_html import DangerouslySetInnerHTML
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from app import app
import json
import datetime
from urllib.parse import urlparse
import dash
import pyperclip
from pycoingecko import CoinGeckoAPI
import pandas as pd


cg = CoinGeckoAPI()
coin_list = cg.get_coins_list()
coin_list_df = pd.DataFrame.from_records(coin_list)
coin_list_df['symbol'] = coin_list_df['symbol'].str.upper()
coin_list_df.set_index('symbol', inplace=True)
layout = html.Div([
    dbc.Row(
        [
            dbc.Form(
                [
                    dbc.FormGroup(
                        [
                            dbc.Input(
                                type="text",
                                placeholder="Enter Symbol or slug",
                                id='crypto-symbol-input'),
                        ], className="mr-3",
                    ),
                    dbc.Button(color="primary", id='crypto-go-button',
                               className='fas fa-paper-plane'),
                ],
                inline=True,
            ),
        ]
    ),
    dbc.Row(html.Br()),
    dbc.Row(dbc.Container(id='crypto-output', fluid=True))
])


@app.callback(
    Output('crypto-output', 'children'),
    [Input('crypto-go-button', 'n_clicks')],
    [State('crypto-symbol-input', 'value')])
def display_value(n_clicks, symbol: str):
    if n_clicks is None:
        raise PreventUpdate
    if symbol is None:
        raise PreventUpdate
    else:
        symbol = symbol.upper()
        try:
            data = cg.get_coin_by_id(
                str(coin_list_df.loc[symbol].id), localization='false')
        except(ValueError, KeyError):
            # treating symbol as slug
            data = cg.get_coin_by_id(
                symbol.lower(), localization='false')
            symbol = data['symbol']
        if not data:
            return dbc.Alert(dcc.Markdown('''
            Could not fetch data for symbol : **{0}**.
            ---
            Check [CoinGecko](https://www.coingecko.com/en)
             or [CoinMarketCap](https://coinmarketcap.com/)
             for a valid symbol.
            '''.format(symbol)), color="danger"),
        with open('config.json', 'r') as file:
            config = json.load(file)['crypto']
        tickers = [ticker for ticker in data['tickers'] if ticker['market']
                   ['identifier'] in config['viewer']['markets']]
        if len(tickers) <= 4 or config['viewer']['markets'][0] == "*":
            tickers = data['tickers']
        tickers = sorted(tickers, key=lambda t: t['market']['identifier'])
        markets = sorted(list(set([t['market']['identifier']
                                   for t in data['tickers']])))
        market_data = get_market_data(data=data)
        stats = {
            "Current Price": f'${market_data["current_price"]["usd"]:,}',
            "Market Cap": f'{market_data["market_cap"]["usd"]:,}',
            "24H Low/High": f'${market_data["low_24h"]["usd"]:,}/${market_data["high_24h"]["usd"]:,}',
            "24H Trading Volume": f'{market_data["total_volume"]["usd"]:,}',
            "Circulating supply": f'{data["market_data"]["circulating_supply"]:,}' if data["market_data"]["circulating_supply"] is not None else "--",
            "Total supply": f'{data["market_data"]["total_supply"]:,}' if data["market_data"]["total_supply"] is not None else "--",
            "Max supply": f'{data["market_data"]["max_supply"]:,}' if data["market_data"]["max_supply"] is not None else "--",
        }
        col1 = {k: market_data[k]
                for k in market_data if "percentage" not in k}
        col2 = {k: market_data[k] for k in market_data if "percentage" in k}
        current_price = data['market_data']['current_price']
        with open('apps/crypto_cp.json', 'w') as file:
            json.dump(current_price, file)
        return [
            dbc.Container(get_ticker_carousel(tickers=tickers),
                          fluid=True),
            html.Hr(),
            dbc.Container(dbc.Row([
                dbc.Col([
                    dbc.Row([html.Img(src=data['image']['small']),
                             html.A(html.H2(data['name']),
                                    href=data['links']['homepage'][0])],
                            align='end', justify='start'),
                    html.Br(),
                    dbc.Row([get_links(data=data)],
                            align='end', justify='start'),
                    html.Br(),
                    dbc.Row([get_social_links(data=data)],
                            align='end', justify='start'),
                    html.Br(),
                    display_contract_address(data=data),
                    html.Br(),
                    get_avalable_markets_popover(markets=markets),
                ]),
                dbc.Col(
                    dbc.Table([
                        html.Tr([
                            html.Td(html.Div(key, style={
                                'float': 'left'})),
                            html.Td(html.Div(value, style={
                                'float': 'right'})),
                        ]) for key, value in stats.items()],
                        hover=True, size='sm', striped=False, borderless=True
                    ), width='auto'
                ),

            ], align='center', justify='center')),
            dbc.Modal([
                dbc.ModalHeader('Description'),
                dbc.ModalBody([
                    DangerouslySetInnerHTML(
                        '<p>' + data['description']['en'] + '</p>')
                ]),
                dbc.ModalFooter(
                    dbc.Button("Close", id="description-modal-close",
                               color='secondary')
                ),
            ], id='description-modal'),
            html.Hr(),
            dbc.Container(fluid=True, children=get_currency_converter(
                current_price=current_price, symbol=data['symbol']),
                style={'width': '50rem'}),
            html.Hr(),
            # dbc.Row(children=[
            dbc.Container(get_currency_tabs(
                col1=col1, col2=col2, config=config)),
            # ]),
            html.Hr(),
            dbc.Container(dbc.Row(get_stats(data=data),
                                  align='start', justify='center',
                                  style={'height': '100rem'}))
        ]


def get_avalable_markets_popover(markets: list):
    return dbc.Container(
        [
            dbc.Button(
                "Markets Available In",
                id="markets-popover-target",
                color="secondary"
            ),
            dbc.Popover(
                [
                    dbc.PopoverHeader("Markets"),
                    dbc.PopoverBody(
                        ", ".join([m.upper() for m in markets]) if markets else "Not Available"),
                ],
                id="markets-popover",
                is_open=False,
                target="markets-popover-target",
            ),
        ]
    )


@app.callback(
    Output("markets-popover", "is_open"),
    [Input("markets-popover-target", "n_clicks")],
    [State("markets-popover", "is_open")],
)
def toggle_popover(n, is_open):
    if n:
        return not is_open
    return is_open


def display_contract_address(data):
    try:
        if data['contract_address'].startswith('0x'):
            return dbc.Row([
                dbc.InputGroup([
                    dbc.InputGroupAddon(
                        'Contract', addon_type='prepend'),
                    dbc.Input(value=data['contract_address'],
                              id='contract-address',
                              disabled=True, plaintext=True),
                    dbc.InputGroupAddon(dbc.Button(id='copy-button',
                                                   className="far fa-clipboard"),
                                        addon_type='append')
                ]),
                html.Div(id='copy-address-output',
                         style={'display': 'none'})
            ], style={'width': '30rem'})
        else:
            return dbc.Row()
    except(KeyError):
        return dbc.Row()


@app.callback(
    Output('copy-address-output', 'children'),
    [Input('copy-button', 'n_clicks')],
    State('contract-address', 'value'))
def myfun(x, address):
    pyperclip.copy(address)
    return ""


@app.callback(
    Output("description-modal", "is_open"),
    [Input("description-modal-open", "n_clicks"),
     Input("description-modal-close", "n_clicks")],
    [State("description-modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


def get_links(data: dict):
    return dbc.ButtonGroup([
        dbc.Button('Description',
                   id='description-modal-open',
                   className="fas fa-expand-alt"),
        dbc.DropdownMenu([
            dbc.DropdownMenuItem(
                urlparse(explorer).netloc,
                href=explorer) for explorer in data['links']['blockchain_site'] if explorer != ""
        ],
            label="Explorers"),
        dbc.DropdownMenu([
            dbc.DropdownMenuItem(
                repo,
                href=repo) for repo in data['links']['repos_url']['github'] if repo != ""
        ],
            label="Github Repos")
    ])


def get_social_links(data: dict):
    buttons = []
    if data['links']['twitter_screen_name'] != "":
        buttons += [dbc.Button(
            'twitter',
            href=f"https://twitter.com/{data['links']['twitter_screen_name']}",
            className='fab fa-twitter', style={"backgroundColor": '#1C9CEA'})]
    if data['links']['facebook_username'] != "":
        buttons += [dbc.Button(
            'facebook',
            href=f"https://facebook.com/{data['links']['facebook_username']}",
            className='fab fa-facebook', style={'backgroundColor': '#3F64AB'})]
    if data['links']['subreddit_url'] != "":
        buttons += [dbc.Button(
            'reddit',
            href=data['links']['subreddit_url'],
            className='fab fa-reddit', style={'backgroundColor': '#F54300'})]
    if data['links']['chat_url'][0] != "":
        buttons += [dbc.Button(
            'discord',
            href=data['links']['chat_url'][0],
            className='fab fa-discord', style={'backgroundColor': '#7289DA'})]

    return dbc.ButtonGroup(children=buttons)


def get_ticker_carousel(tickers):
    return dtc.Carousel([
        dbc.Card([
            dbc.CardBody([
                        html.H6(ticker['market']['name'],
                                className="card-subtitle"),
                        html.H4(
                            f"{get_base_name(ticker)} / {ticker['target']}",
                            className='card-title'),
                        html.H5(
                            f"Last Price: {ticker['last']: .7f}",
                            className="card-text"),
                        html.P(
                            f"Volume: {round(ticker['volume'], 2)}",
                            className="card-text"),
                        dbc.CardLink(
                            'Trade URL', href=ticker['trade_url'],
                            className='fas fa-link'),
                        ], className='card-block text-center'),
        ], color='secondary',
            style={"height": "11rem", "border-radius": "15px"})
        for ticker in tickers],
        slides_to_scroll=1,
        swipe_to_slide=True,
        variable_width=True,
        center_mode=False,
        infinite=True,
        autoplay=True,
        speed=2000,
        arrows=False
    )


def get_base_name(ticker):
    if len(ticker['base']) > 6:
        return ticker['coin_id'].upper()
    return ticker['base']


def get_stats(data: dict):
    return [
        dbc.Col([
            html.H5('Social Stats'), dbc.ListGroup([
                dbc.ListGroupItem([
                    dbc.ListGroupItemHeading(" ".join(key.title().split("_"))),
                    dbc.ListGroupItemText(value)
                ]) for key, value in data['community_data'].items()
                if value is not None] + [dbc.ListGroupItem([
                    dbc.ListGroupItemHeading('Alexa Ranking'),
                    dbc.ListGroupItemText(
                        data['public_interest_stats']['alexa_rank'])
                ])]
            )]),
        dbc.Col([html.H5('Github Stats'), dbc.ListGroup([
            dbc.ListGroupItem([
                dbc.ListGroupItemHeading(" ".join(key.title().split("_"))),
                dbc.ListGroupItemText(value)
            ]) for key, value in data['developer_data'].items()
            if not isinstance(value, dict)]
        )]),
        dbc.Col([html.H5('Community Stats'), dbc.ListGroup([
            dbc.ListGroupItem([
                dbc.ListGroupItemHeading('Market Cap Rank'),
                dbc.ListGroupItemText(data['market_cap_rank'])
            ]),
            dbc.ListGroupItem([
                dbc.ListGroupItemHeading('CoinGecko Rank'),
                dbc.ListGroupItemText(data['coingecko_rank'])
            ]),
            dbc.ListGroupItem([
                dbc.ListGroupItemHeading('CoinGecko Score'),
                dbc.ListGroupItemText(data['coingecko_score'])
            ]),
            dbc.ListGroupItem([
                dbc.ListGroupItemHeading('Developer Score'),
                dbc.ListGroupItemText(data['developer_score'])
            ]),
            dbc.ListGroupItem([
                dbc.ListGroupItemHeading('Community Score'),
                dbc.ListGroupItemText(data['community_score'])
            ]),
            dbc.ListGroupItem([
                dbc.ListGroupItemHeading('Liquidity Score'),
                dbc.ListGroupItemText(data['liquidity_score'])
            ]),
            dbc.ListGroupItem([
                dbc.ListGroupItemHeading('Public Interest Score'),
                dbc.ListGroupItemText(data['public_interest_score'])
            ]),
        ])])
    ]


def get_market_data(data):
    market_data = data['market_data'].copy()
    del market_data['roi']
    del market_data['price_change_24h']
    del market_data['price_change_percentage_24h']
    del market_data['price_change_percentage_7d']
    del market_data['price_change_percentage_14d']
    del market_data['price_change_percentage_30d']
    del market_data['price_change_percentage_60d']
    del market_data['price_change_percentage_200d']
    del market_data['price_change_percentage_1y']
    del market_data['market_cap_change_24h']
    del market_data['market_cap_change_percentage_24h']
    del market_data['market_cap_rank']
    del market_data['fully_diluted_valuation']
    del market_data['total_supply']
    del market_data['max_supply']
    del market_data['circulating_supply']
    del market_data['last_updated']

    for key in list(market_data):
        if "_in_currency" in key:
            new_key = key.replace("_in_currency", "")
            market_data[new_key] = market_data[key]
            del market_data[key]
    return market_data


def get_currency_tabs(col1, col2, config):
    return dbc.Tabs([
                    dbc.Tab(
                        dbc.Container(dbc.Row([
                            dbc.Col(dbc.Table([
                                html.Tr([
                                    html.Td(
                                        html.Div(
                                            " ".join(key.title().split("_")),
                                            style={'float': 'left'})),
                                    html.Td(
                                        html.Div(
                                            pretty_print(value[curr]),
                                            style={'float': 'right'})),
                                ]) for key, value in col1.items() if value],
                                hover=True,
                                size='sm',
                                borderless=True
                            )),
                            dbc.Col(dbc.Table([
                                html.Tr([
                                    html.Td(
                                        html.Div(
                                            " ".join(key.title().split("_")),
                                            style={'float': 'left'})),
                                    html.Td(
                                        html.Div(
                                            pretty_print(value[curr]),
                                            style={'float': 'right'})),
                                ]) for key, value in col2.items() if value],
                                hover=True,
                                size='sm',
                                borderless=True
                            )), ])), label=curr.upper(),
                        labelClassName="text-info"
                    ) for curr in config['viewer']['pref_curr']
                    ])


def pretty_print(value):
    try:
        return round(value, 2)
    except(Exception):
        return datetime.datetime.strptime(value,
                                          "%Y-%m-%dT%H:%M:%S.%fZ").date()


@app.callback(
    Output('result-side-1', 'value'),
    [Input('curr-select-1', 'value'), Input('eth-side-1', 'value')],
    [State('eth-side-1', 'value'), State('curr-select-1', 'value')]
)
def convert_from_eth(*args):
    ctx = dash.callback_context
    with open('apps/crypto_cp.json', 'r') as file:
        cp = json.load(file)
    amount = ctx.states['eth-side-1.value']
    currency = ctx.states['curr-select-1.value']
    if amount is None or currency is None:
        raise PreventUpdate
    else:
        return round(amount*cp[currency], 3)


@app.callback(
    Output('eth-side-2', 'value'),
    [Input('curr-select-2', 'value'), Input('result-side-2', 'value')],
    [State('result-side-2', 'value'), State('curr-select-2', 'value')]
)
def convert_to_eth(*args):
    ctx = dash.callback_context
    with open('apps/crypto_cp.json', 'r') as file:
        cp = json.load(file)
    amount = ctx.states['result-side-2.value']
    currency = ctx.states['curr-select-2.value']
    if amount is None or currency is None:
        raise PreventUpdate
    else:
        return f'{amount/cp[currency]: .7f}'


def get_currency_converter(current_price, symbol):
    all_curr = current_price.keys()
    return [dbc.Row([
        dbc.Col(
            dbc.InputGroup([
                dbc.Input(id='eth-side-1', type="number", value=1, step=1),
                dbc.InputGroupAddon(symbol.upper(), addon_type="append")
            ]),
        ),
        dbc.Col(dbc.Select(id='curr-select-1',
                           options=[
                               {'label': curr.upper(),
                                'value': curr} for curr in all_curr
                           ],
                           value='usd',
                           )),
        dbc.Col(dbc.Input(id='result-side-1', disabled=True)),
    ], align='center', justify='center'
    ),
        html.Br(),
        dbc.Row([
            dbc.Col(dbc.Input(id='result-side-2',
                              type="number", step=1, value=1)),
            dbc.Col(dbc.Select(id='curr-select-2',
                               options=[
                                   {'label': curr.upper(),
                                    'value': curr} for curr in all_curr
                               ],
                               value='usd',
                               )),
            dbc.Col(
                dbc.InputGroup([
                    dbc.Input(id='eth-side-2', disabled=True),
                    dbc.InputGroupAddon(symbol.upper(), addon_type="append")
                ]),
            ),
        ], align='center', justify='center'
    )]
