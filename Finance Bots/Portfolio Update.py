#### THANKS TO REDDIT USER VANDERVS FOR PROVIDING THE BONES ####

import requests
import os
from dotenv import load_dotenv

load_dotenv()

# API Endpoints and variables
secret = os.getenv("NOTION_SECRET")
base_db_url = "https://api.notion.com/v1/databases/"
base_pg_url = "https://api.notion.com/v1/pages/"
base_crypto_url = "https://api.coinlore.net/api/"
base_stock_url = "https://yh-finance.p.rapidapi.com/stock/v2/get-summary"



# Notion tokens
wallet_db_id = os.getenv("FINANCE_DB_ID")
data = {}
header = {"Authorization":secret, "Notion-Version":"2021-05-13", "Content-Type": "application/json"}

# Query Notion database
response = requests.post(base_db_url + wallet_db_id + "/query", headers=header, data=data)

for page in response.json()["results"]:
    page_id = page["id"]
    props = page['properties']

    asset_type = props['Type']['select']['name']
    
    asset_code = props['Code']['rich_text'][0]['plain_text']

    # Common stock listed on the ASX
    if asset_type == "Stock":

        stock_query_string = {"symbol": asset_code + ".AX","region":"AU"}
        stock_headers = {
            'x-rapidapi-host': "yh-finance.p.rapidapi.com",
            'x-rapidapi-key': os.getenv("RAPID_API_KEY")
        }
        response = requests.request("GET", base_stock_url, headers=stock_headers, params=stock_query_string).json()
       
        stock_price = response['price']['regularMarketPrice']['raw']
        stock_open_price  = response['price']['regularMarketOpen']['raw']

        # Format for notion database
        data_price = '{"properties": {"Price": { "number":' + str(stock_price) + '},\
                                        "Market Open": { "number":' + str(stock_open_price) + '}, \
                                        "URL": { "url": "https://finance.yahoo.com/quote/' + asset_code + '.AX"}}}'
        # Send to notion database                        
        send_price = requests.patch(base_pg_url + page_id, headers=header, data=data_price)

    # Crypto stock 
    if asset_type == "Crypto":

        #Get ID from table
        try:
            crypto_id = str(props['CoinloreID']['number'])
        #If ID does not exist then find ID with loop
        except:
            crypto_id = None
            api_page = 0
            while crypto_id == None:
                #NOT UPDATING  on loop
                request_by_code = requests.get(base_crypto_url + "tickers/?start=" + str(api_page * 100) + "&limit=100").json()['data']
                print(base_crypto_url + "tickers/?start=" + str(api_page * 100) + "&limit=100")
                 #Search for code
                for item in request_by_code:
                    if item["symbol"] == asset_code:
                        crypto_id = item["id"]
                api_page += 1
        # Make request for data with ID
        crypto_request = requests.get(base_crypto_url + "ticker/?id=" + crypto_id)
      
        
        # Need to make new request if not within first 100 coins
        # coin = next((item for item in request_by_code if item["symbol"] == asset_code), None)

         
        if (crypto_request.status_code == 200):
            coin_info = crypto_request.json()[0]
            price = coin_info['price_usd']
            price_btc = coin_info['price_btc'] 
            pcent_1h = coin_info['percent_change_1h']
            pcent_24h = coin_info['percent_change_24h']
            pcent_7days = coin_info['percent_change_7d']
            coin_url = "https://coinmarketcap.com/currencies/" + coin_info['nameid']

            # Format for notion database
            data_price = '{"properties":   \
                            { \
                                "Price": { "number":' + str(price) + '}, \
                                "price btc": { "number":' + str(price_btc) + '}, \
                                "% 1H": { "number":' + str(pcent_1h) + '}, \
                                "% 24H": { "number":' + str(pcent_24h) + '}, \
                                "% 7days": { "number":' + str(pcent_7days) + '}, \
                                "CoinloreID": { "number":' + crypto_id + '}, \
                                "URL": { "url": "https://coinmarketcap.com/currencies/' + coin_info['nameid'] + '"}}}'
            # Send to notion database
            send_price = requests.patch(base_pg_url + page_id, headers=header, data=data_price)
     

            