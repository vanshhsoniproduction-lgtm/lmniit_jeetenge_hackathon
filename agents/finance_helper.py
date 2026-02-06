import requests
import json
import re
from django.conf import settings

def get_coingecko_price(token_ids):
    """
    Fetches simple price and 24h change for a list of token IDs.
    Returns a dictionary keyed by token_id.
    """
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ",".join(token_ids),
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }
    
    # Check for API Key in settings
    api_key = getattr(settings, 'COINGECKO_API_KEY', None)
    if api_key:
        params['x_cg_demo_api_key'] = api_key
        
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"CoinGecko Error: {e}")
    return {}

def extract_holdings(user_input):
    """
    Parses user input string like "2 ETH, 5000 DOGE" into a list of dicts.
    Returns: [{'symbol': 'ETH', 'amount': 2.0}, ...]
    """
    # Regex to find number + word patterns
    # e.g. "2.5 ETH" or "1000 USDC"
    matches = re.findall(r'(\d+(?:\.\d+)?)\s*([a-zA-Z]+)', user_input)
    
    holdings = []
    for amount, symbol in matches:
        holdings.append({
            "symbol": symbol.upper(),
            "amount": float(amount)
        })
    
    # If no matches found, maybe it's just an investment amount
    if not holdings and "$" in user_input:
        # Try to extract dollar amount
        dollar_match = re.search(r'\$?(\d+(?:\.\d+)?)', user_input)
        if dollar_match:
            return [{"symbol": "USD", "amount": float(dollar_match.group(1))}]

    return holdings

def get_market_context_for_gemini(holdings):
    """
    Prepares a context string with live prices to feed into Gemini.
    """
    # Map common symbols to CoinGecko IDs (Simple mapping)
    symbol_map = {
        "BTC": "bitcoin", "ETH": "ethereum", "MON": "monad", "SOL": "solana",
        "DOGE": "dogecoin", "MATIC": "matic-network", "USDC": "usd-coin",
        "USDT": "tether", "ADA": "cardano", "XRP": "ripple", "DOT": "polkadot"
    }
    
    ids_to_fetch = []
    info_list = []

    for h in holdings:
        sym = h['symbol']
        if sym in symbol_map:
            ids_to_fetch.append(symbol_map[sym])
        
        info_list.append(f"{h['amount']} {sym}")

    market_data = {}
    if ids_to_fetch:
        market_data = get_coingecko_price(ids_to_fetch)
    
    # Construct Context String
    context = "User Holdings:\n" + ", ".join(info_list) + "\n\nLive Market Data (CoinGecko):\n"
    
    total_value = 0.0
    
    for h in holdings:
        sym = h['symbol']
        if sym in symbol_map:
            cg_id = symbol_map[sym]
            if cg_id in market_data:
                data = market_data[cg_id]
                price = data.get('usd', 0)
                change = data.get('usd_24h_change', 0)
                value = h['amount'] * price
                total_value += value
                
                context += f"- {sym}: ${price} (24h: {change:.2f}%) | Val: ${value:.2f}\n"
            else:
                context += f"- {sym}: No live data found.\n"
        else:
            context += f"- {sym}: Unknown symbol (assume $1 placeholder for analysis).\n"
            if sym == "USD": total_value += h['amount']

    return context, total_value
