import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import dash_daq as daq
from app import app
from ScreenerTicker import STicker
from yahooquery import Ticker
from googlesearch import search
from bs4 import BeautifulSoup
import requests
import plotly.express as px
import pandas as pd
# import dash_trich_components as dtc


layout = html.Div([
    dbc.Row(
        [
            dbc.Form(
                [
                    dbc.FormGroup(
                        [
                            dbc.Input(
                                type="text",
                                placeholder="Enter Symbol",
                                id='symbol-input'),
                        ], className="mr-3",
                    ),
                    dbc.Button(color="primary", id='go-button',
                               className='fas fa-paper-plane'),
                ],
                inline=True,
            ),
        ]
    ),
    dbc.Col(html.Div(id='output'))
])


@app.callback(
    Output('output', 'children'),
    [Input('go-button', 'n_clicks')],
    [State('symbol-input', 'value')])
def display_value(n_clicks, symbol: str):
    if n_clicks is None:
        raise PreventUpdate
    if symbol is None:
        raise PreventUpdate
    else:
        symbol = symbol.upper().strip()
        ticker = symbol + ".NS"
        yTicker = Ticker(ticker)
        yearly_pricing_data = yTicker.history(
            period='1y', interval='1d').loc[ticker]
        yearly_pricing_data = yearly_pricing_data.reset_index()
        pricing = yTicker.price[ticker]
        sTicker = STicker(symbol=symbol)
        yt_asset_profile = yTicker.asset_profile[ticker]
        moneycontrol_url = get_moneycontrol_url(symbol=symbol)
        moneycontrol_data = get_moneycontrol_data(moneycontrol_url)
        key_stats = sTicker.get_key_stats()
        return html.Div([dbc.Row(dbc.Container(
            [
                html.H1(sTicker.get_company_name(), className="display-3"),
                get_links(sTicker=sTicker, moneycontrol_url=moneycontrol_url),
                html.H4(f"Industry : {yt_asset_profile['industry']}"),
                html.H4(f"Sector : {yt_asset_profile['sector']}"),
                html.Hr(className="my-2"),
                dbc.Row([
                    dbc.Col([
                        dbc.Row(html.Br()),
                        get_ohlc_data(pricing=pricing),
                        dbc.Row(html.Br()),
                        dbc.Row(dbc.Col(
                            dcc.Graph(figure=get_ytd_chart(
                                yearly_pricing_data))
                        )),
                        dbc.Row(html.Br()),
                        dbc.Row(get_ranges(pricing,
                                           moneycontrol_data),
                                justify='center')

                    ]),
                    dbc.Col([
                        dbc.Row(get_company_description(sTicker=sTicker)),
                        dbc.Row(html.Br()),
                        dbc.Row(get_key_stats(
                            key_stats, yTicker, ticker, pricing)),
                        dbc.Row(html.Br()),
                    ])
                ])

            ], fluid=True
        )),
            dbc.Row(dbc.Container(html.Div(), style={'height': '3rem'})),
            dbc.Row(dbc.Container(get_tables(sTicker), fluid=True,
                                  style={'height': '50rem'}))
        ])


def get_tables(sTicker: STicker):
    return dbc.Tabs([
        dbc.Tab(dbc.Table.from_dataframe(sTicker.get_quarterly_results(
        ), striped=True, bordered=True, hover=True),
            label='Quaterly Results', labelClassName="text-info"),
        dbc.Tab(dbc.Table.from_dataframe(sTicker.get_profit_and_loss(
        ), striped=True, bordered=True, hover=True),
            label='Profit and Loss', labelClassName="text-info"),
        dbc.Tab(dbc.Table.from_dataframe(sTicker.get_balance_sheet(
        ), striped=True, bordered=True, hover=True),
            label='Balance Sheet', labelClassName="text-info"),
        dbc.Tab(dbc.Table.from_dataframe(sTicker.get_cash_flow(
        ), striped=True, bordered=True, hover=True),
            label='Cash Flow', labelClassName="text-info"),
        dbc.Tab(dbc.Table.from_dataframe(sTicker.get_shareholder_pattern(
        ), striped=True, bordered=True, hover=True),
            label='Shareholder Pattern', labelClassName="text-info"),
        dbc.Tab(dbc.Table.from_dataframe(sTicker.get_industry_peer_comparison(
        ), striped=True, bordered=True, hover=True),
            label='Peer Comparison', labelClassName="text-success"),
    ])


def get_links(sTicker: STicker, moneycontrol_url):
    return dbc.ButtonGroup([
        dbc.Button("Company", color="link",
                   href=sTicker.get_company_link(),
                   external_link=True, className='fas fa-link'),
        dbc.Button("Screener", color="link",
                   href=sTicker.get_screener_link(),
                   external_link=True, className='fas fa-link'),
        dbc.Button("Moneycontrol", color="link",
                   href=moneycontrol_url,
                   external_link=True, className='fas fa-link'),
        dbc.Button(["NSE"], color="link",
                   href=sTicker.get_nse_link(),
                   external_link=True, className='fas fa-link'),
        dbc.Button("BSE", color="link",
                   href=sTicker.get_bse_link(),
                   external_link=True, className='fas fa-link')
    ])


def get_card(title, text, color):
    return dbc.Card(
        dbc.CardBody([
            html.H4(title,
                    className="card-title"),
            html.H5(text, className="card-text"),
        ],
            className='card-block text-center'),
        className='card align-items-center',
        color=color
    )


def get_ohlc_data(pricing):
    return dbc.Container(
        dbc.Row([
            dbc.Col(
                get_card(pricing['regularMarketOpen'], 'Open', 'info')
            ),
            dbc.Col(
                get_card(pricing['regularMarketDayHigh'], 'High', 'primary')
            ),
            dbc.Col(
                get_card(pricing['regularMarketDayLow'], 'Low', 'primary')
            ),
            dbc.Col(
                get_card(pricing['regularMarketPrice'], 'Close', 'info')
            ),
        ]), fluid=True
    )


def get_key_stats(key_stats, yTicker, ticker, pricing):
    stats1 = pd.DataFrame(
        {
            "Stat": [
                "Market Cap ₹(Cr.)",
                "50 Day Average",
                "Volume",
                "High / Low ₹",
                "ROCE %"
            ],
            "Value": [
                key_stats['Market Cap'],
                round(yTicker.summary_detail
                      [ticker]
                      ['fiftyDayAverage'], 2),
                pricing["regularMarketVolume"],
                key_stats['High / Low'],
                key_stats['ROCE']
            ],
        }
    )
    stats2 = pd.DataFrame(
        {
            "Stat": [
                "Stock P/E",
                "Book Value ₹",
                "Face Value ₹",
                "Previous Close",
                "Percentage Change %"
            ],
            "Value": [
                key_stats['Stock P/E'],
                key_stats['Book Value'],
                key_stats['Face Value'],
                pricing['regularMarketPreviousClose'],
                round(pricing["regularMarketChangePercent"]*100, 2)
            ],
        }
    )
    return dbc.Container(dbc.Row([
        dbc.Col(
            dbc.Table([
                html.Tr([
                    html.Td(html.Div(row['Stat'], style={
                        'float': 'left'})),
                    html.Td(html.Div(row['Value'], style={
                        'float': 'right'})),
                ]) for index, row in stats1.iterrows()],
                hover=True, size='sm'
            ), align='center'
        ),
        dbc.Col(
            dbc.Table([
                html.Tr([
                    html.Td(html.Div(row['Stat'], style={
                        'float': 'left'})),
                    html.Td(html.Div(row['Value'], style={
                        'float': 'right'})),
                ]) for index, row in stats2.iterrows()],
                hover=True, size='sm'
            ), align='center'
        ),
    ]))


def get_range(label, value, min_, max_):
    return daq.Slider(
        min=min_,
        max=max_,
        value=value,
        disabled=True,
        marks={str(min_): f'{label}_Low_'+str(min_),
               str(max_): f'{label}_High_'+str(max_)},
        color={"gradient": True,
               'ranges': {'red': [min_, value],
                          'green': [value, max_]}}
    )


def get_ranges(pricing, moneycontrol_data):
    return [
        dbc.Col(
            dbc.Container(
                get_range(label="52W",
                          value=pricing['regularMarketPrice'],
                          min_=moneycontrol_data['52_week_range']
                          ['low'],
                          max_=moneycontrol_data['52_week_range']
                          ['high'],
                          ))),
        dbc.Col(
            dbc.Container(
                get_range(label="Day",
                          value=pricing['regularMarketPrice'],
                          min_=pricing['regularMarketDayLow'],
                          max_=pricing['regularMarketDayHigh'],
                          )))
    ]


def get_company_description(sTicker):
    return dbc.Card([
        dbc.CardHeader(html.H5("About the Company",
                               className="card-title")),
        dbc.CardBody(
            html.P(sTicker.get_company_description()))],
        color="dark", outline=True, inverse=True)


def get_moneycontrol_url(symbol):
    gen = search(f'{symbol} moneycontrol', tld='co.in',
                 num=1, stop=1, pause=3)
    return next(gen)


def get_moneycontrol_data(link):
    data = {}
    soup = BeautifulSoup(requests.get(link).content, 'html.parser')
    data['52_week_range'] = {}
    data['52_week_range']['low'] = float(
        soup.find('div', id='sp_yearlylow').string)
    data['52_week_range']['high'] = float(
        soup.find('div', id='sp_yearlyhigh').string)
    return data


def get_ytd_chart(pricing):
    fig = px.line(pricing,
                  x='date', y='close')
    fig.update_xaxes(visible=True, fixedrange=True,
                     showgrid=False, spikemode='toaxis')
    fig.update_yaxes(visible=True, fixedrange=True,
                     showgrid=False, spikemode='toaxis')
    fig.update_layout(annotations=[], overwrite=True)
    fig.update_layout(height=220,
                      showlegend=False,
                      plot_bgcolor="#222222",
                      paper_bgcolor="#222222",
                      margin=dict(t=0, l=0, b=0, r=0),
                      font={'color': "#FFFFFF"})
    return fig
