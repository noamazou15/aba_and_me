import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st
import pandas as pd


def get_data(ticker, start_date= '2000-01-01', end_date = pd.to_datetime('today').strftime('%Y-%m-%d')):
    df = yf.download(ticker, start=start_date, end=end_date, interval='1wk')
    window_size = 3
    log_returns = np.log(df['Adj Close'] / df['Adj Close'].shift(1))
    rolling_std_dev = log_returns.rolling(window=window_size).std()
    rolling_annualized_volatility = rolling_std_dev * np.sqrt(52)
    df['Volatility'] = rolling_annualized_volatility
    df['weekly_change'] = df['Adj Close'].pct_change() * 100
    return df

def get_volatility_range(df, num_std_devs = 1):
    curr_volatility = df['Volatility'][-1]
    std = df['Volatility'].std()
    return (curr_volatility - num_std_devs * std, curr_volatility + num_std_devs * std)

def filter_volatility_range(df, a, b):
    return df[(df['Volatility'] >= a) & (df['Volatility'] <= b)]


def get_bounds_for_running_prob(weekly_changes_within_volatility_range):
    bounds = {}
    for percentile in range(5, 50, 5):
        percentile = percentile / 100
        range_lower, range_upper = weekly_changes_within_volatility_range.quantile(percentile), weekly_changes_within_volatility_range.quantile(1-percentile)
        bounds[int((1-(percentile * 2)) * 100)] = (range_lower, range_upper)
    #dict to df
    bounds_df = pd.DataFrame(bounds.items(), columns=['Percentile', 'Bounds'])
    return bounds_df

def get_percent_for_bound(a,b, weekly_changes_within_volatility_range):
    return len(weekly_changes_within_volatility_range[(weekly_changes_within_volatility_range >= a) & (weekly_changes_within_volatility_range <= b)]) / len(weekly_changes_within_volatility_range) * 100


# Modified section for calculating percentage within custom bounds to display in table format
def main():
    st.title('Stock Volatility and Change Analysis')

    # Initialization of session state variables if they don't exist
    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'filtered_df' not in st.session_state:
        st.session_state.filtered_df = None
    if 'a' not in st.session_state:
        st.session_state.a = 0
    if 'b' not in st.session_state:
        st.session_state.b = 0
    if 'curr_price' not in st.session_state:
        st.session_state.curr_price = 0

    # User input for stock ticker
    ticker = st.text_input('Enter stock ticker (e.g. AAPL):', 'AAPL').upper()
    #displat current stock price
    # Display the analysis based on inputs
    if st.button('Fetch Data'):
        # Fetching and storing stock data in session state
        st.session_state.df = get_data(ticker)
        
        # Calculating and storing volatility range in session state
        st.session_state.a, st.session_state.b = get_volatility_range(st.session_state.df)
        st.session_state.filtered_df = filter_volatility_range(st.session_state.df, st.session_state.a, st.session_state.b)
        st.session_state.curr_price = st.session_state.df["Close"].iloc[-1]
        st.write(f'Current {ticker} stock price: {st.session_state.curr_price:.2f}')

    if st.session_state.df is not None and st.session_state.filtered_df is not None:
        # Section for displaying bounds for running probability
        if st.checkbox('Show Bounds for Running Probability'):
            bounds_msg = get_bounds_for_running_prob(st.session_state.filtered_df['weekly_change'])
            st.write('Bounds for running probability:')
            st.table(bounds_msg)
            
        # Section for calculating percentage within custom bounds
        if st.checkbox('Calculate Percentage within Custom Bounds'):
            # Inputs for calculating percentage within custom bounds
            st.write('Calculate the percentage of weekly changes within custom bounds:')
            custom_a = st.number_input('Enter lower bound for analysis:', value=st.session_state.a, key='custom_a')
            custom_b = st.number_input('Enter upper bound for analysis:', value=st.session_state.b, key='custom_b')
            calculate_button = st.button('Calculate Percentage', key='calculate_percentage')
            if calculate_button:
                percent_within_bounds = get_percent_for_bound(custom_a, custom_b, st.session_state.filtered_df['weekly_change'])
                # Creating a pandas DataFrame to display the results as a table
                results_df = pd.DataFrame({
                    'Metric': ['Percentage of weekly changes within range'],
                    'Value': [f'{percent_within_bounds:.2f}%'],
                    'Range': [f'{custom_a:.2f} to {custom_b:.2f}'],
                    'Range In Dollars': [f'{st.session_state.curr_price * (100+custom_a)/100 :.2f} to {st.session_state.curr_price * (100+custom_b)/100 :.2f}']
                })
                st.table(results_df)

if __name__ == '__main__':
    main()

