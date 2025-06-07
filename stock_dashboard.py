# Stock Market Dashboard
# Complete Streamlit application for stock market analysis

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Stock Market Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .sidebar-header {
        font-size: 1.5rem;
        color: #333;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Main title
st.markdown('<h1 class="main-header">📈 Stock Market Dashboard</h1>', unsafe_allow_html=True)

# Sidebar for user inputs
st.sidebar.markdown('<h2 class="sidebar-header">🔧 Configuration</h2>', unsafe_allow_html=True)

# Stock selection
popular_stocks = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'ADBE', 'CRM']
selected_stock = st.sidebar.selectbox("Select Stock Symbol", popular_stocks + ['Custom'])

if selected_stock == 'Custom':
    custom_stock = st.sidebar.text_input("Enter Stock Symbol", "AAPL")
    stock_symbol = custom_stock.upper()
else:
    stock_symbol = selected_stock

# Date range selection
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input("Start Date", datetime.now() - timedelta(days=365))
with col2:
    end_date = st.date_input("End Date", datetime.now())

# Analysis type
analysis_type = st.sidebar.selectbox(
    "Analysis Type",
    ["Overview", "Technical Analysis", "Price Prediction", "Comparison"]
)

@st.cache_data
def load_stock_data(symbol, start, end):
    """Load stock data from Yahoo Finance"""
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(start=start, end=end)
        info = stock.info
        return data, info
    except:
        return None, None

@st.cache_data
def calculate_technical_indicators(data):
    """Calculate technical indicators"""
    # Moving averages
    data['MA20'] = data['Close'].rolling(window=20).mean()
    data['MA50'] = data['Close'].rolling(window=50).mean()
    
    # RSI
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands
    data['BB_middle'] = data['Close'].rolling(window=20).mean()
    bb_std = data['Close'].rolling(window=20).std()
    data['BB_upper'] = data['BB_middle'] + (bb_std * 2)
    data['BB_lower'] = data['BB_middle'] - (bb_std * 2)
    
    return data

def predict_stock_price(data, days=30):
    """Simple linear regression prediction"""
    if len(data) < 50:
        return None, None
    
    # Prepare data
    data_reset = data.reset_index()
    data_reset['Days'] = range(len(data_reset))
    
    X = data_reset[['Days']].values
    y = data_reset['Close'].values
    
    # Train model
    model = LinearRegression()
    model.fit(X, y)
    
    # Predict future prices
    future_days = np.arange(len(data), len(data) + days).reshape(-1, 1)
    future_prices = model.predict(future_days)
    
    # Create future dates
    last_date = data.index[-1]
    future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=days)
    
    return future_dates, future_prices

# Load data
with st.spinner(f"Loading data for {stock_symbol}..."):
    stock_data, stock_info = load_stock_data(stock_symbol, start_date, end_date)

if stock_data is not None and not stock_data.empty:
    # Calculate technical indicators
    stock_data = calculate_technical_indicators(stock_data)
    
    # Company information
    if stock_info:
        st.markdown("## 🏢 Company Information")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Company", stock_info.get('longName', 'N/A'))
        with col2:
            st.metric("Sector", stock_info.get('sector', 'N/A'))
        with col3:
            st.metric("Market Cap", f"${stock_info.get('marketCap', 0):,.0f}" if stock_info.get('marketCap') else 'N/A')
        with col4:
            st.metric("P/E Ratio", f"{stock_info.get('trailingPE', 0):.2f}" if stock_info.get('trailingPE') else 'N/A')
    
    # Current metrics
    current_price = stock_data['Close'].iloc[-1]
    previous_price = stock_data['Close'].iloc[-2]
    price_change = current_price - previous_price
    price_change_pct = (price_change / previous_price) * 100
    
    st.markdown("## 📊 Current Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Current Price", f"${current_price:.2f}", f"{price_change:+.2f} ({price_change_pct:+.2f}%)")
    with col2:
        st.metric("Volume", f"{stock_data['Volume'].iloc[-1]:,.0f}")
    with col3:
        st.metric("52W High", f"${stock_data['High'].max():.2f}")
    with col4:
        st.metric("52W Low", f"${stock_data['Low'].min():.2f}")
    
    # Analysis based on selection
    if analysis_type == "Overview":
        st.markdown("## 📈 Price Chart")
        
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=stock_data.index,
            open=stock_data['Open'],
            high=stock_data['High'],
            low=stock_data['Low'],
            close=stock_data['Close'],
            name=stock_symbol
        ))
        
        fig.update_layout(
            title=f"{stock_symbol} Stock Price",
            yaxis_title="Price ($)",
            xaxis_title="Date",
            template="plotly_white",
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Volume chart
        st.markdown("## 📊 Volume Analysis")
        vol_fig = px.bar(
            x=stock_data.index,
            y=stock_data['Volume'],
            title=f"{stock_symbol} Trading Volume"
        )
        vol_fig.update_layout(template="plotly_white", height=400)
        st.plotly_chart(vol_fig, use_container_width=True)
    
    elif analysis_type == "Technical Analysis":
        st.markdown("## 🔍 Technical Analysis")
        
        # Price with moving averages
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Close'], name='Close Price'))
        fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['MA20'], name='MA20'))
        fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['MA50'], name='MA50'))
        
        fig.update_layout(
            title=f"{stock_symbol} - Price with Moving Averages",
            yaxis_title="Price ($)",
            template="plotly_white",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Bollinger Bands
        bb_fig = go.Figure()
        bb_fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['BB_upper'], name='Upper Band', line=dict(dash='dash')))
        bb_fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Close'], name='Close Price'))
        bb_fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['BB_lower'], name='Lower Band', line=dict(dash='dash')))
        
        bb_fig.update_layout(
            title=f"{stock_symbol} - Bollinger Bands",
            yaxis_title="Price ($)",
            template="plotly_white",
            height=500
        )
        st.plotly_chart(bb_fig, use_container_width=True)
        
        # RSI
        rsi_fig = px.line(x=stock_data.index, y=stock_data['RSI'], title=f"{stock_symbol} - RSI")
        rsi_fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
        rsi_fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
        rsi_fig.update_layout(template="plotly_white", height=400)
        st.plotly_chart(rsi_fig, use_container_width=True)
    
    elif analysis_type == "Price Prediction":
        st.markdown("## 🔮 Price Prediction")
        
        prediction_days = st.slider("Days to Predict", 1, 90, 30)
        
        future_dates, future_prices = predict_stock_price(stock_data, prediction_days)
        
        if future_dates is not None:
            # Plot historical and predicted prices
            pred_fig = go.Figure()
            pred_fig.add_trace(go.Scatter(
                x=stock_data.index,
                y=stock_data['Close'],
                name='Historical Price',
                line=dict(color='blue')
            ))
            pred_fig.add_trace(go.Scatter(
                x=future_dates,
                y=future_prices,
                name='Predicted Price',
                line=dict(color='red', dash='dash')
            ))
            
            pred_fig.update_layout(
                title=f"{stock_symbol} - Price Prediction",
                yaxis_title="Price ($)",
                template="plotly_white",
                height=600
            )
            st.plotly_chart(pred_fig, use_container_width=True)
            
            # Prediction summary
            predicted_price = future_prices[-1]
            prediction_change = predicted_price - current_price
            prediction_change_pct = (prediction_change / current_price) * 100
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Price", f"${current_price:.2f}")
            with col2:
                st.metric("Predicted Price", f"${predicted_price:.2f}")
            with col3:
                st.metric("Expected Change", f"{prediction_change:+.2f} ({prediction_change_pct:+.2f}%)")
            
            st.warning("⚠️ This is a simple linear regression model for demonstration purposes. Real trading decisions should be based on comprehensive analysis and professional advice.")
    
    elif analysis_type == "Comparison":
        st.markdown("## ⚖️ Stock Comparison")
        
        comparison_stocks = st.multiselect(
            "Select stocks to compare",
            popular_stocks,
            default=['AAPL', 'GOOGL', 'MSFT']
        )
        
        if comparison_stocks:
            comparison_data = {}
            for symbol in comparison_stocks:
                data, _ = load_stock_data(symbol, start_date, end_date)
                if data is not None:
                    comparison_data[symbol] = data['Close']
            
            if comparison_data:
                comp_df = pd.DataFrame(comparison_data)
                
                # Normalize prices to show percentage change
                normalized_df = comp_df.div(comp_df.iloc[0]) * 100
                
                comp_fig = px.line(
                    normalized_df,
                    title="Stock Performance Comparison (Normalized to 100)",
                    labels={"value": "Normalized Price", "index": "Date"}
                )
                comp_fig.update_layout(template="plotly_white", height=600)
                st.plotly_chart(comp_fig, use_container_width=True)
                
                # Performance metrics
                st.markdown("### Performance Metrics")
                metrics_data = []
                for symbol in comparison_stocks:
                    if symbol in comp_df.columns:
                        start_price = comp_df[symbol].iloc[0]
                        end_price = comp_df[symbol].iloc[-1]
                        total_return = ((end_price - start_price) / start_price) * 100
                        volatility = comp_df[symbol].pct_change().std() * np.sqrt(252) * 100
                        
                        metrics_data.append({
                            'Symbol': symbol,
                            'Total Return (%)': f"{total_return:.2f}%",
                            'Volatility (%)': f"{volatility:.2f}%",
                            'Current Price': f"${end_price:.2f}"
                        })
                
                metrics_df = pd.DataFrame(metrics_data)
                st.dataframe(metrics_df, use_container_width=True)
    
    # Data table
    with st.expander("📋 Raw Data"):
        st.dataframe(stock_data.tail(20))

else:
    st.error(f"❌ Could not load data for {stock_symbol}. Please check the symbol and try again.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>📈 Stock Market Dashboard | Built with Streamlit & Python</p>
    <p>⚠️ This tool is for educational purposes only. Not financial advice.</p>
</div>
""", unsafe_allow_html=True)