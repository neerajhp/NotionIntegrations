import requests

# API Endpoints and variables
secret = "secret_34x8c7nklHcI22r8P6E0OAWeUYd7fYjXOL42GQ1WkzH"
base_db_url = "https://api.notion.com/v1/databases/"
base_pg_url = "https://api.notion.com/v1/pages/"
base_crypto_url = "https://api.coinlore.net/api/tickers/"
base_stock_url = "https://www.shikhersrivastava.com/stocktradingapi/stock/quote?symbol="

wallet_db_id = "e475f449040a41ab974dd90195847551"
data = {}
header = {"Authorization":secret, "Notion-Version":"2021-05-13", "Content-Type": "application/json"}

# Query Notion database
response = requests.post(base_db_url + wallet_db_id + "/query", headers=header, data=data)



for page in response.json()["results"]:
    page_id = page["id"]
    props = page['properties']

    asset_type = props['Type']['select']['name']
    
    asset_code = props['Code']['rich_text'][0]['plain_text']

    if asset_type == "Stock":
        response = requests.get(base_stock_url + asset_code).json()
        
        
        stock_price = response[asset_code]['latestPrice']
        pcent_1h = "{:.2f}".format(100*response[asset_code]['changePercent'])
        pcent_24h = "{:.2f}".format(response[asset_code]['ytdChange'])

        data_price = '{"properties": {"Price": { "number":' + str(stock_price) + '},\
                                        "% 1H": { "number":' + str(pcent_1h) + '}, \
                                        "% 24H": { "number":' + str(pcent_24h) + '}, \
                                        "URL": { "url": "https://finance.yahoo.com/quote/' + asset_code + '"}}}'
                                        
        send_price = requests.patch(base_pg_url + page_id, headers=header, data=data_price)
        print(data_price)

    if asset_type == "Crypto":

        #Get ID from table
        try:
            crypto_id = props['CoinloreID']['number']
        #If ID does not exist then find ID with loop
        except:
            crypto_id = None
            api_page = 1
            while crypto_id == None:
                request_by_code = requests.get(base_crypto_url + "?start=" + str(api_page * 100) + " &limit=100").json()['data']
                 #Search for code
                for item in request_by_code:
                    if item["symbol"] == asset_code:
                        crypto_id = item["id"]
                api_page += 1
        # Make request for data with ID
      
        
        # Need to make new request if not within first 100 coins
        coin = next((item for item in request_by_code if item["symbol"] == asset_code), None)

         
        if(request_by_code != []):
            price = coin['price_usd']
            price_btc = coin['price_btc'] 
            pcent_1h = coin['percent_change_1h']
            pcent_24h = coin['percent_change_24h']
            pcent_7days = coin['percent_change_7d']
            coin_url = "https://coinmarketcap.com/currencies/" + coin['nameid']

            data_price = '{"properties":   \
                            {"Price": { "number":' + str(price) + '},\
                            "price btc": { "number":' + str(price_btc) + '}, \
                            "% 1H": { "number":' + str(pcent_1h) + '}, \
                            "% 24H": { "number":' + str(pcent_24h) + '}, \
                            "% 7days": { "number":' + str(pcent_7days) + '}, \
                            "URL": { "url":"' + coin_url + '"}}}'
        
            send_price = requests.patch(base_pg_url + page_id, headers=header, data=data_price)
            