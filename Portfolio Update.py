import requests

secret = "your secret"
base_db_url = "https://api.notion.com/v1/databases/"
base_pg_url = "https://api.notion.com/v1/pages/"
base_crypto_url = "https://api.coinlore.net/api/tickers/?start=0&limit=100"
base_stock_url = "https://www.shikhersrivastava.com/stocktradingapi/stock/quote?symbol="

wallet_db_id = "id of database Wallet above"
data = {}
header = {"Authorization":secret, "Notion-Version":"2021-05-13", "Content-Type": "application/json"}

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
        request_by_code = requests.get(base_crypto_url).json()['data']
    
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
            