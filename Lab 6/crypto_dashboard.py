import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import requests
import pandas as pd
import numpy as np

# Initialize Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = 'Cryptocurrency Dashboard'

# Fetch global market data
def fetch_global_data():
    url = "https://api.coingecko.com/api/v3/global"
    r = requests.get(url)
    if r.status_code != 200:
        return 0, 0, 0  # or handle differently
    
    json_data = r.json()
    if "data" not in json_data:
        return 0, 0, 0  # or handle differently
    
    data = json_data["data"]
    total_market_cap = data["total_market_cap"]["usd"]
    total_24h_volume = data["total_volume"]["usd"]
    btc_dominance = data["market_cap_percentage"]["btc"]
    return total_market_cap, total_24h_volume, btc_dominance

# Fetch cryptocurrency data
def fetch_crypto_data(symbol, currency='USD', days=30):
    url = f'https://api.coingecko.com/api/v3/coins/{symbol}/market_chart?vs_currency={currency}&days={days}&interval=daily'
    response = requests.get(url)
    data = response.json()
    
    # Check if the needed keys exist
    if 'prices' not in data or 'total_volumes' not in data:
        print("API response is missing 'prices' or 'total_volumes'. Response data:", data)
        return pd.DataFrame(), pd.DataFrame()  # return empty frames or handle differently
    
    df = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    df_volume = pd.DataFrame(data['total_volumes'], columns=['timestamp', 'volume'])
    df_volume['timestamp'] = pd.to_datetime(df_volume['timestamp'], unit='ms')
    
    # Standard moving averages
    df['7-day MA'] = df['price'].rolling(7).mean()
    df['30-day MA'] = df['price'].rolling(30).mean()
    df['Price Change %'] = df['price'].pct_change() * 100
    
    # Calculate Bollinger Bands
    df['20-day MA'] = df['price'].rolling(20).mean()
    df['Std Dev'] = df['price'].rolling(20).std()
    df['Upper Band'] = df['20-day MA'] + (df['Std Dev'] * 2)
    df['Lower Band'] = df['20-day MA'] - (df['Std Dev'] * 2)
    
    # Calculate RSI (14-day)
    delta = df['price'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Calculate MACD
    df['12-day EMA'] = df['price'].ewm(span=12, adjust=False).mean()
    df['26-day EMA'] = df['price'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['12-day EMA'] - df['26-day EMA']
    df['Signal Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD Histogram'] = df['MACD'] - df['Signal Line']
    
    # Calculate Daily Return and Cumulative Return
    df['Daily Return'] = df['price'].pct_change()
    df['Cumulative Return'] = (1 + df['Daily Return']).cumprod() - 1
    
    return df, df_volume

# Fetch global market overview data once
global_total_market_cap, global_24h_volume, btc_dominance = fetch_global_data()

# Layout with collapsible left panel, global overview, and multi-column chart layout
app.layout = html.Div([
    # Header
    html.Div(
        html.H1("Cryptocurrency Dashboard", style={'textAlign': 'center', 'color': '#ffffff'}),
        style={'backgroundColor': '#343a40', 'padding': '20px', 'borderRadius': '10px', 'marginBottom': '20px'}
    ),

    # Global Market Overview Cards
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H4("Total Market Cap", className="card-title"),
                    html.H2(f"${global_total_market_cap:,.0f}", className="card-text")
                ])
            ], color="primary", inverse=True),
            width=4
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H4("24h Volume", className="card-title"),
                    html.H2(f"${global_24h_volume:,.0f}", className="card-text")
                ])
            ], color="info", inverse=True),
            width=4
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.H4("BTC Dominance", className="card-title"),
                    html.H2(f"{btc_dominance:,.2f}%", className="card-text")
                ])
            ], color="warning", inverse=True),
            width=4
        )
    ], style={'marginBottom': '20px'}),

    # Main layout
    dbc.Row([
        # Collapsible side panel
        dbc.Col([
            dbc.Button(
                "Toggle Controls", id="toggle-button", color="primary", className="mb-3", n_clicks=0,
                style={'width': '100%', 'fontSize': '16px'}
            ),
            dbc.Collapse(
                html.Div([
                    html.H3("Controls", style={'textAlign': 'center', 'marginBottom': '20px', 'color': '#343a40'}),
                    
                    html.Label("Select Cryptocurrency:", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='crypto-symbol',
                        options=[
                            {'label': 'Bitcoin', 'value': 'bitcoin'},
                            {'label': 'Ethereum', 'value': 'ethereum'},
                            {'label': 'Dogecoin', 'value': 'dogecoin'},
                            {'label': 'Cardano', 'value': 'cardano'},
                            {'label': 'Solana', 'value': 'solana'}
                        ],
                        value='bitcoin',
                        style={'marginBottom': '20px'}
                    ),
                    
                    html.Label("Select Time Range:", style={'fontWeight': 'bold'}),
                    dcc.RadioItems(
                        id='time-range',
                        options=[
                            {'label': '7 Days', 'value': '7'},
                            {'label': '14 Days', 'value': '14'},
                            {'label': '30 Days', 'value': '30'},
                            {'label': '90 Days', 'value': '90'},
                            {'label': '180 Days', 'value': '180'},
                            {'label': '365 Days', 'value': '365'}
                        ],
                        value='30',
                        labelStyle={'display': 'block', 'margin': '10px 0'}
                    ),
                    
                    html.Hr(),
                    
                    html.Div([
                        html.P("Data provided by CoinGecko API", style={'fontSize': '0.8em', 'fontStyle': 'italic'}),
                        html.P("Last updated: " + pd.Timestamp.now().strftime("%Y-%m-%d"), style={'fontSize': '0.8em'})
                    ], style={'marginTop': '30px', 'textAlign': 'center'})
                ], style={
                    'padding': '20px', 
                    'backgroundColor': '#f8f9fa', 
                    'borderRadius': '10px', 
                    'boxShadow': '0 4px 8px 0 rgba(0,0,0,0.2)'
                }),
                id="collapse", is_open=True
            )
        ], width=3, style={'backgroundColor': '#f8f9fa', 'padding': '10px', 'borderRadius': '10px'}),
        
        # Charts in multi-column layout (rearranged)
        dbc.Col([
            # Row 1: Price Change + MACD
            dbc.Row([
                dbc.Col(dcc.Graph(id='crypto-price-change-chart', style={'boxShadow': '0 4px 8px rgba(0,0,0,0.2)'}), width=6),
                dbc.Col(dcc.Graph(id='macd-chart', style={'boxShadow': '0 4px 8px rgba(0,0,0,0.2)'}), width=6)
            ], style={'marginBottom': '20px'}),
            # Row 2: Price + Volume
            dbc.Row([
                dbc.Col(dcc.Graph(id='crypto-price-chart', style={'boxShadow': '0 4px 8px rgba(0,0,0,0.2)'}), width=6),
                dbc.Col(dcc.Graph(id='crypto-volume-chart', style={'boxShadow': '0 4px 8px rgba(0,0,0,0.2)'}), width=6)
            ], style={'marginBottom': '20px'}),
            # Row 3: Moving Average + Comparison
            dbc.Row([
                dbc.Col(dcc.Graph(id='crypto-moving-average-chart', style={'boxShadow': '0 4px 8px rgba(0,0,0,0.2)'}), width=6),
                dbc.Col(dcc.Graph(id='crypto-comparison-chart', style={'boxShadow': '0 4px 8px rgba(0,0,0,0.2)'}), width=6)
            ], style={'marginBottom': '20px'}),
            # Row 4: Bollinger + RSI
            dbc.Row([
                dbc.Col(dcc.Graph(id='bollinger-bands-chart', style={'boxShadow': '0 4px 8px rgba(0,0,0,0.2)'}), width=6),
                dbc.Col(dcc.Graph(id='rsi-chart', style={'boxShadow': '0 4px 8px rgba(0,0,0,0.2)'}), width=6)
            ], style={'marginBottom': '20px'}),
            # Row 5: Cumulative Return
            dbc.Row([
                dbc.Col(dcc.Graph(id='cumulative-return-chart', style={'boxShadow': '0 4px 8px rgba(0,0,0,0.2)'}), width=6)
            ])
        ], width=9)
    ])
])

# Callback to toggle the collapsible side panel
@app.callback(
    Output("collapse", "is_open"),
    [Input("toggle-button", "n_clicks")],
    [dash.dependencies.State("collapse", "is_open")]
)
def toggle_collapse(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

# Callback to update cryptocurrency charts
@app.callback(
    [Output('crypto-price-chart', 'figure'), 
     Output('crypto-volume-chart', 'figure'), 
     Output('crypto-moving-average-chart', 'figure'), 
     Output('crypto-comparison-chart', 'figure'), 
     Output('crypto-price-change-chart', 'figure'),
     Output('bollinger-bands-chart', 'figure'),
     Output('rsi-chart', 'figure'),
     Output('macd-chart', 'figure'),
     Output('cumulative-return-chart', 'figure')],
    [Input('crypto-symbol', 'value'),
     Input('time-range', 'value')]
)
def update_crypto_charts(symbol, time_range):
    df, df_volume = fetch_crypto_data(symbol, days=int(time_range))
    
    # Price Chart
    price_fig = go.Figure()
    price_fig.add_trace(go.Scatter(x=df['timestamp'], y=df['price'], mode='lines', name='Price'))
    price_fig.update_layout(
        title=f'{symbol.capitalize()} Price Trend ({time_range} Days)', 
        xaxis_title='Date', 
        yaxis_title='Price (USD)',
        template='plotly_white'
    )
    
    # Volume Chart
    volume_fig = go.Figure()
    volume_fig.add_trace(go.Bar(x=df_volume['timestamp'], y=df_volume['volume'], name='Volume', marker_color='blue'))
    volume_fig.update_layout(
        title=f'{symbol.capitalize()} Trading Volume ({time_range} Days)', 
        xaxis_title='Date', 
        yaxis_title='Volume',
        template='plotly_white'
    )
    
    # Moving Average Chart
    ma_fig = go.Figure()
    ma_fig.add_trace(go.Scatter(x=df['timestamp'], y=df['price'], mode='lines', name='Price'))
    ma_fig.add_trace(go.Scatter(x=df['timestamp'], y=df['7-day MA'], mode='lines', name='7-day MA', line=dict(dash='dash', color='red')))
    ma_fig.add_trace(go.Scatter(x=df['timestamp'], y=df['30-day MA'], mode='lines', name='30-day MA', line=dict(dash='dot', color='green')))
    ma_fig.update_layout(
        title=f'{symbol.capitalize()} Moving Averages ({time_range} Days)', 
        xaxis_title='Date', 
        yaxis_title='Price (USD)',
        template='plotly_white'
    )
    
    # Price vs Volume Comparison Chart
    comparison_fig = go.Figure()
    comparison_fig.add_trace(go.Scatter(x=df['timestamp'], y=df['price'], mode='lines', name='Price', yaxis='y1'))
    comparison_fig.add_trace(go.Bar(x=df_volume['timestamp'], y=df_volume['volume'], name='Volume', marker_color='blue', yaxis='y2', opacity=0.7))
    comparison_fig.update_layout(
        title=f'{symbol.capitalize()} Price vs Volume ({time_range} Days)',
        xaxis_title='Date',
        yaxis={'title': 'Price (USD)', 'side': 'left'},
        yaxis2={'title': 'Volume', 'side': 'right', 'overlaying': 'y'},
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        template='plotly_white'
    )
    
    # Price Change Percentage Chart
    price_change_fig = go.Figure()
    price_change_fig.add_trace(go.Bar(
        x=df['timestamp'], 
        y=df['Price Change %'], 
        name='Price Change %',
        marker_color=np.where(df['Price Change %'] >= 0, 'green', 'red')
    ))
    price_change_fig.update_layout(
        title=f'{symbol.capitalize()} Daily Price Change (%) ({time_range} Days)', 
        xaxis_title='Date', 
        yaxis_title='Percentage Change',
        template='plotly_white'
    )
    
    # Bollinger Bands Chart
    bollinger_fig = go.Figure()
    bollinger_fig.add_trace(go.Scatter(
        x=df['timestamp'], 
        y=df['Upper Band'], 
        mode='lines', 
        name='Upper Band', 
        line=dict(width=1, color='rgba(173, 204, 255, 0.7)'),
        showlegend=True
    ))
    bollinger_fig.add_trace(go.Scatter(
        x=df['timestamp'], 
        y=df['Lower Band'], 
        mode='lines', 
        name='Lower Band', 
        line=dict(width=1, color='rgba(173, 204, 255, 0.7)'),
        fill='tonexty', 
        fillcolor='rgba(173, 204, 255, 0.2)',
        showlegend=True
    ))
    bollinger_fig.add_trace(go.Scatter(x=df['timestamp'], y=df['20-day MA'], mode='lines', name='20-day MA', line=dict(width=2, color='rgba(44, 130, 201, 1)')))
    bollinger_fig.add_trace(go.Scatter(x=df['timestamp'], y=df['price'], mode='lines', name='Price', line=dict(width=2, color='black')))
    bollinger_fig.update_layout(
        title=f'{symbol.capitalize()} Bollinger Bands ({time_range} Days)', 
        xaxis_title='Date', 
        yaxis_title='Price (USD)',
        template='plotly_white',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5)
    )
    
    # RSI Chart
    rsi_fig = go.Figure()
    rsi_fig.add_trace(go.Scatter(x=df['timestamp'], y=df['RSI'], mode='lines', name='RSI', line=dict(color='purple', width=2)))
    # Add overbought/oversold reference lines
    rsi_fig.add_shape(
        type='line', x0=df['timestamp'].min(), x1=df['timestamp'].max(), y0=70, y1=70,
        line=dict(color='red', dash='dash')
    )
    rsi_fig.add_shape(
        type='line', x0=df['timestamp'].min(), x1=df['timestamp'].max(), y0=30, y1=30,
        line=dict(color='green', dash='dash')
    )
    rsi_fig.add_annotation(x=df['timestamp'].max(), y=70, text="Overbought", showarrow=False, xshift=10)
    rsi_fig.add_annotation(x=df['timestamp'].max(), y=30, text="Oversold", showarrow=False, xshift=10)
    rsi_fig.update_layout(
        title=f'{symbol.capitalize()} RSI (14-day) ({time_range} Days)',
        xaxis_title='Date',
        yaxis_title='RSI',
        yaxis=dict(range=[0, 100]),
        template='plotly_white'
    )
    
    # MACD Chart
    macd_fig = go.Figure()
    macd_fig.add_trace(go.Bar(
        x=df['timestamp'], 
        y=df['MACD Histogram'], 
        name='Histogram',
        marker_color=np.where(df['MACD Histogram'] >= 0, 'rgba(0, 153, 0, 0.7)', 'rgba(255, 51, 51, 0.7)')
    ))
    macd_fig.add_trace(go.Scatter(x=df['timestamp'], y=df['MACD'], mode='lines', name='MACD', line=dict(color='blue', width=2)))
    macd_fig.add_trace(go.Scatter(x=df['timestamp'], y=df['Signal Line'], mode='lines', name='Signal', line=dict(color='red', width=1.5)))
    macd_fig.update_layout(
        title=f'{symbol.capitalize()} MACD ({time_range} Days)',
        xaxis_title='Date',
        yaxis_title='MACD',
        template='plotly_white',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5)
    )
    
    # Cumulative Return Chart
    cum_return_fig = go.Figure()
    cum_return_fig.add_trace(go.Scatter(
        x=df['timestamp'], 
        y=df['Cumulative Return']*100, 
        mode='lines', 
        name='Cumulative Return',
        line=dict(color='darkblue', width=2),
        fill='tozeroy', 
        fillcolor='rgba(0, 0, 255, 0.1)'
    ))
    cum_return_fig.update_layout(
        title=f'{symbol.capitalize()} Cumulative Return ({time_range} Days)', 
        xaxis_title='Date', 
        yaxis_title='Cumulative Return (%)',
        template='plotly_white'
    )
    
    return (price_fig, volume_fig, ma_fig, comparison_fig, price_change_fig,
            bollinger_fig, rsi_fig, macd_fig, cum_return_fig)

# Run server
if __name__ == '__main__':
    app.run(debug=True)