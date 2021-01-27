import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.express as px
from app import app
import pandas as pd
import numpy as np
import json
import requests

MAX_SHARPE = 'max_sharpe'
MIN_VOL = 'min_vol'

layout = dbc.Container([
    dbc.Form([
        dbc.FormGroup(
            [
                dbc.InputGroup([
                    dbc.InputGroupAddon("Symbols", addon_type="prepend"),
                    dbc.Input(type="text", id="c-optimize-symbols-input",
                              placeholder="Enter comma separated symbols."
                              + " eg: AAA,BBB,CCCC")
                ], style={'width': '30rem'}),
                dbc.InputGroup([
                    dbc.InputGroupAddon("Frequency", addon_type="prepend"),
                    dbc.Select(id='c-optimize-freq-select',
                               options=[
                                   {"label": "day", "value": "day"},
                                   {"label": "hour", "value": "hour"},
                                   {"label": "minute", "value": "minute"}
                               ],
                               value='day',
                               )]),
                dbc.InputGroup([
                    dbc.InputGroupAddon("Data Points", addon_type="prepend"),
                    dbc.Input(type="number", id="c-optimize-dp-input",
                              placeholder="Enter number of data points",
                              value=365)]),
                dbc.InputGroup([
                    dbc.InputGroupAddon(
                        "Number of Portfolios", addon_type="prepend"),
                    dbc.Input(type="number", id="c-optimize-ports-input",
                              placeholder="Enter number of portfolios",
                              value=50000)]),
                dbc.InputGroup([
                    dbc.InputGroupAddon(
                        "Risk Free Rate", addon_type="prepend"),
                    dbc.Input(type="number", id="c-optimize-rfr-input",
                              placeholder="Enter risk free rate",
                              value=0.04),
                    dbc.InputGroupAddon(
                        dbc.Button(' Optimize', color="primary",
                                   id='c-optimize-go-button',
                                   className='fas fa-balance-scale',),
                        addon_type='append')
                ]),
            ],
        ),
    ], inline=True,),
    dbc.Row([
        dbc.Label(id='c-optimize-form-feedback')
    ]),
    dbc.Row(html.Br()),
    dbc.Row(dbc.Spinner(dbc.Container(
        id='c-optimize-output', fluid=True), type="grow"),
        justify='center'),
    dbc.Row(html.Br()),
    dbc.Row(dbc.Spinner(dbc.Container(
        id='c-rebalance-output', fluid=True), type='grow'),
        justify='center'),
    dcc.Store(id='optimization-results')
], fluid=True)


@app.callback([
    Output('c-optimize-form-feedback', 'children'),
    Output('c-optimize-symbols-input', 'valid'),
    Output('c-optimize-symbols-input', 'invalid'),
    Output('c-optimize-ports-input', 'valid'),
    Output('c-optimize-ports-input', 'invalid'),
    Output('c-optimize-dp-input', 'valid'),
    Output('c-optimize-dp-input', 'invalid'),
    Output('c-optimize-rfr-input', 'valid'),
    Output('c-optimize-rfr-input', 'invalid'),
],
    [
        Input('c-optimize-symbols-input', 'value'),
        Input('c-optimize-ports-input', 'value'),
        Input('c-optimize-dp-input', 'value'),
        Input('c-optimize-rfr-input', 'value'),
],
    [
        State('c-optimize-symbols-input', 'value'),
        State('c-optimize-ports-input', 'value'),
        State('c-optimize-dp-input', 'value'),
        State('c-optimize-rfr-input', 'value'),
]
)
def form_feedback(*args):
    ctx = dash.callback_context
    feedback_text = ''
    symbols = ctx.states['c-optimize-symbols-input.value']
    ports = ctx.states['c-optimize-ports-input.value']
    dp = ctx.states['c-optimize-dp-input.value']
    rfr = ctx.states['c-optimize-rfr-input.value']
    symbols_bool = symbols is None or symbols == ''
    ports_bool = ports is None or ports <= 0
    dp_bool = dp is None or dp <= 0
    rfr_bool = rfr is None
    if symbols_bool:
        feedback_text += 'Symbols required!!'
    if ports_bool:
        feedback_text += ' Number of portfolios has to be positive number!!'
    if dp_bool:
        feedback_text += ' Number of data points has to be positive number!!'
    if rfr_bool:
        feedback_text += ' Risk free rate cannot be empty!!'
    return feedback_text, not symbols_bool, symbols_bool, not ports_bool, ports_bool, not dp_bool, dp_bool, not rfr_bool, rfr_bool


@app.callback(
    [
        Output('c-optimize-output', 'children'),
        Output('optimization-results', 'data')
    ],
    [
        Input('c-optimize-go-button', 'n_clicks')
    ],
    [
        State('c-optimize-symbols-input', 'value'),
        State('c-optimize-freq-select', 'value'),
        State('c-optimize-dp-input', 'value'),
        State('c-optimize-ports-input', 'value'),
        State('c-optimize-rfr-input', 'value'),
    ])
def display_optimize_output(n_clicks, symbols: str,
                            freq: str, no_of_data_points: int,
                            num_portfolios: int, rfr: float):
    data = pd.DataFrame()
    if n_clicks is None:
        raise PreventUpdate
    if symbols is None:
        raise PreventUpdate
    if num_portfolios <= 0:
        raise PreventUpdate
    if no_of_data_points <= 0:
        raise PreventUpdate
    else:
        try:
            with open('config.json', 'r') as file:
                config = json.load(file)['crypto']
            api_key = config['crypto_compare_api_key']
            if api_key == "":
                return dbc.Alert(dcc.Markdown('''
                API key not provided in config.json.
                Please get api key from
                [CryptoComapre](https://min-api.cryptocompare.com)
                '''), color="danger"),
            symbol_list = [symbol.strip() for symbol in symbols.split(',')]
            print("Symbols:", ','.join(symbol_list))
            for symbol in symbol_list:
                data[symbol] = get_crypto_data(
                    symbol, api_key, frequency=freq,
                    no_of_data_points=no_of_data_points,
                    exchange=None)['Close']
            data = data[(data != 0).all(1)]
            symbol_dict = {s: 0 for s in symbol_list}
            layout, optimization_results = show_optimization_results(
                assets=symbol_list, data=data,
                num_portfolios=num_portfolios, rfr=rfr)
            result = dbc.Col([
                dbc.Row(dcc.Graph(figure=get_corr_matrix_heatmap(data)),
                        align='center', justify='center'),
                dbc.Row(dbc.Col(layout),
                        align='center', justify='center'),
                dbc.Row(
                    dbc.InputGroup(
                        [
                            dbc.InputGroupAddon(
                                "Portfolio",
                                addon_type="prepend"),
                            dbc.Textarea(id="c-portfolio-text-area-input",
                                         value=json.dumps(
                                             symbol_dict, indent=4),
                                         bs_size='lg',
                                         style={'height': '20rem'}),
                            dbc.InputGroupAddon(
                                dbc.Button("Rebalance",
                                           id="c-rebalance-button",
                                           color='primary'),
                                addon_type="append",
                            ),
                        ],
                    ),
                )
            ])
            return result, optimization_results
        except Exception as e:
            return dbc.Alert(dcc.Markdown('''
            Exception occured {0}: {1}
            '''.format(e)), color="danger"), {}


@app.callback(
    Output("c-rebalance-output", "children"),
    Input("c-rebalance-button", "n_clicks"),
    [
        State("c-portfolio-text-area-input", "value"),
        State('optimization-results', 'data')
    ]
)
def display_rebalance_output(n_clicks, text_area: str, results):
    if not n_clicks:
        raise PreventUpdate
    if not text_area:
        raise PreventUpdate
    if not results:
        raise PreventUpdate
    try:
        portfolio = json.loads(text_area)
    except(Exception):
        return dbc.Alert("Invalid JSON format", color="danger"),
    min_vol = results[MIN_VOL]['Expected Weights']
    max_sharpe = results[MAX_SHARPE]['Expected Weights']
    symbols = portfolio.keys()
    with open('config.json', 'r') as file:
        config = json.load(file)['crypto']
    api_key = config['crypto_compare_api_key']
    url = 'https://min-api.cryptocompare.com/data/pricemulti'
    params = {
        "fsyms": ','.join(symbols),
        "tsyms": "USD",
        "api_key": api_key
    }
    exchange_rate = requests.get(url, params=params).json()
    usd_price = {key: value['USD'] for key, value in exchange_rate.items()}
    display_result = {}
    results = pd.DataFrame(
        {"a": portfolio, 'usd_price': usd_price})
    results['holding'] = results['a'] * results['usd_price']
    results['w'] = results['holding']/results['holding'].sum()
    total_asset_value = results['holding'].sum()
    for entry in [('Maximmum Sharpe Ratio', max_sharpe),
                  ('Minimmum Volatitly', min_vol)]:
        results['ew'] = pd.Series(entry[1])
        results['ew_r'] = results['ew']-results['w']
        results['ew_usd'] = results['ew_r'] * \
            results['holding'].sum()
        results['ew_a'] = results['ew_usd']/results['usd_price']
        display_result[entry[0]] = results['ew_a'].to_dict()
    return [html.H4(f'Total Asset Value: ${total_asset_value:.4f}'),
            html.Hr()] +\
        [dbc.Row(dbc.Col([
            html.H5(name),
            dbc.ListGroup([
                dbc.ListGroupItem([
                    dbc.ListGroupItemHeading(f"{value:.5f} {key}"),
                    dbc.ListGroupItemText(f"{value*usd_price[key]:=.2f} USD"),
                ]) for key, value in ew.items()
            ], horizontal=True),
            html.Hr()
        ]),
            align='center', justify='center'
        ) for name, ew in display_result.items()] +\
        [dbc.Label("* positive value is for buy" +
                   " and negative value is for sell")]


def get_corr_matrix_heatmap(data: pd.DataFrame):
    returns = np.log(data / data.shift(1))
    fig = px.imshow(returns.corr(),
                    labels=dict(x="Coins", y="Coins", color="Correlation"),)
    fig.update_layout(showlegend=True,
                      plot_bgcolor="#000000",
                      paper_bgcolor="#222222",
                      font={'color': "#FFFFFF"})
    return fig


def get_crypto_data(symbol, api_key, to_symbol='USD', frequency='day',
                    exchange='Binance', no_of_data_points=100):
    if frequency == 'day' or frequency == 'hour' or frequency == 'minute':
        link = 'https://min-api.cryptocompare.com/data/v2/histo'+frequency
        params = {
            "fsym": symbol,
            "tsym": to_symbol,
            "limit": no_of_data_points,
            "api_key": api_key
        }
        if exchange is not None:
            params['e'] = exchange
        data_json = requests.get(link, params=params).json()
        data_dict = data_json['Data']['Data']
        df = pd.DataFrame(data_dict,
                          columns=['close', 'high', 'low', 'open',
                                   'time', 'volumefrom', 'volumeto'],
                          dtype='float64')
        posix_time = pd.to_datetime(df['time'], unit='s')
        df.insert(0, "Date", posix_time)
        df.drop("time", axis=1, inplace=True)
        df.index = df['Date']
        df.rename(columns={'close': 'Close', 'high': 'High', 'open': 'Open',
                           'low': 'Low', 'volumeto': 'Volume'}, inplace=True)
        return df
    else:
        return pd.DataFrame()


def portfolio_annualised_performance(weights, mean_returns,
                                     cov_matrix, no_of_days):
    returns = np.sum(np.dot(mean_returns, weights)) * no_of_days
    std = np.sqrt(np.dot(weights.T, np.dot(
        cov_matrix, weights))) * np.sqrt(no_of_days)
    return std, returns


def fetch_expected_weights(assets: list, d: pd.DataFrame,
                           num_portfolios: int = 10000,
                           rfr=0.05, no_of_days=365):

    returns = np.log(d / d.shift(1))
    mean_returns = returns.mean()
    cov_matrix = returns.cov()
    num_assets = len(assets)
    port_returns = []
    port_volatility = []
    sharpe_ratio = []
    stock_weights = []

    for i in range(num_portfolios):
        weights = np.random.random_sample(num_assets)
        weights /= np.sum(weights)
        volatility, ret = portfolio_annualised_performance(
            weights, mean_returns, cov_matrix, no_of_days)
        stock_weights.append(weights)
        port_returns.append(ret)
        port_volatility.append(volatility)
        sharpe = (ret-rfr) / volatility
        sharpe_ratio.append(sharpe)

    portfolio = {'Returns': port_returns,
                 'Volatility': port_volatility,
                 'Sharpe Ratio': sharpe_ratio}
    for counter, symbol in enumerate(assets):
        portfolio[symbol] = [Weight[counter] for Weight in stock_weights]
    df = pd.DataFrame(portfolio)
    column_order = ['Returns', 'Volatility', 'Sharpe Ratio']
    column_order = column_order + [stock for stock in assets]
    df = df[column_order]
    max_sharpe = df['Sharpe Ratio'].max()
    min_volatility = df['Volatility'].min()
    max_sharpe_port = df.loc[df['Sharpe Ratio'] == max_sharpe]
    min_volatility_port = df.loc[df['Volatility'] == min_volatility]
    return get_dict_result(min_volatility_port),\
        get_dict_result(max_sharpe_port)


def get_dict_result(portfolio: pd.DataFrame):
    transpose = portfolio.T
    results = {}
    results['Returns'] = portfolio['Returns'].values[0]
    results['Volatility'] = portfolio['Volatility'].values[0]
    results['Sharpe Ratio'] = portfolio['Sharpe Ratio'].values[0]
    transpose.drop(['Returns', 'Volatility', 'Sharpe Ratio'], inplace=True)
    transpose.columns = ['Expected Weights']
    results.update(transpose.to_dict())
    return results


def show_optimization_results(assets, data,
                              num_portfolios: int = 10000,
                              rfr=0.05, no_of_days=365):
    min_vol, max_sharpe = fetch_expected_weights(assets=assets, d=data,
                                                 num_portfolios=num_portfolios,
                                                 rfr=rfr,
                                                 no_of_days=no_of_days)
    results = {}
    results[MIN_VOL] = min_vol
    results[MAX_SHARPE] = max_sharpe
    return [
        html.Hr(),
        dbc.Row(html.H3('Max Sharpe Portfolio'),
                align='center', justify='center'),
        dbc.Row(
            dbc.ListGroup([
                dbc.ListGroupItem([
                    dbc.ListGroupItemHeading(f'{max_sharpe["Returns"]:.2%}'),
                    dbc.ListGroupItemText('RETURNS')
                ]),
                dbc.ListGroupItem([
                    dbc.ListGroupItemHeading(
                        f'{max_sharpe["Volatility"]:.4f}'),
                    dbc.ListGroupItemText("VOLATILITY")
                ]),
                dbc.ListGroupItem([
                    dbc.ListGroupItemHeading(
                        f'{max_sharpe["Sharpe Ratio"]:.4f}'),
                    dbc.ListGroupItemText("SHARPE RATIO")
                ]),
            ], horizontal=True),
            align='center', justify='center'
        ),
        dbc.Row(dbc.ListGroup([
            dbc.ListGroupItem([
                dbc.ListGroupItemHeading(f'{weight:.2%}'),
                dbc.ListGroupItemText(symbol)
            ]) for symbol, weight in max_sharpe['Expected Weights'].items()
        ], horizontal=True),
            align='center', justify='center'),
        html.Hr(),
        dbc.Row(html.H3('Min Volatitlity Portfolio'),
                align='center', justify='center'),
        dbc.Row(
            dbc.ListGroup([
                dbc.ListGroupItem([
                    dbc.ListGroupItemHeading(f'{min_vol["Returns"]:.2%}'),
                    dbc.ListGroupItemText('RETURNS')
                ]),
                dbc.ListGroupItem([
                    dbc.ListGroupItemHeading(
                        f'{min_vol["Volatility"]:.4f}'),
                    dbc.ListGroupItemText("VOLATILITY")
                ]),
                dbc.ListGroupItem([
                    dbc.ListGroupItemHeading(
                        f'{min_vol["Sharpe Ratio"]:.4f}'),
                    dbc.ListGroupItemText("SHARPE RATIO")
                ]),
            ], horizontal=True),
            align='center', justify='center'
        ),
        dbc.Row(dbc.ListGroup([
            dbc.ListGroupItem([
                dbc.ListGroupItemHeading(f'{weight:.2%}'),
                dbc.ListGroupItemText(symbol)
            ]) for symbol, weight in min_vol['Expected Weights'].items()
        ], horizontal=True),
            align='center', justify='center'),
        html.Hr(),
    ], results
