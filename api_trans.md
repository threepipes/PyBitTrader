start 81279:40000


今使われているapi
# 注文 sendchildorder

## bitflyer

POST /v1/me/sendchildorder

### param

{
  "product_code": "BTC_JPY",
  "child_order_type": "LIMIT",
  "side": "BUY",
  "price": 30000,
  "size": 0.1,
  "minute_to_expire": 10000,
  "time_in_force": "GTC"
}

### response

{
    "child_order_acceptance_id": "JRF20150707-050237-639234"
}

## coincheck

POST /api/exchange/orders

### param

{rate: 30000, amount: 10, order_type: "buy", pair: "btc_jpy"}

*pair 取引ペア。現在は "btc_jpy" のみです。 
*order_type 注文方法 
rate 注文のレート。（例）28000 
amount 注文での量。（例）0.1 
market_buy_amount 成行買で利用する日本円の金額。（例）10000 
position_id 決済するポジションのID 
stop_loss_rate 逆指値レート

### response

{
  "success": true,
  "id": 12345,
  "rate": "30010.0",
  "amount": "1.3",
  "order_type": "sell",
  "stop_loss_rate": null,
  "pair": "btc_jpy",
  "created_at": "2015-01-10T05:55:38.000Z"
}


# 資産状況 getbalance

## bitflyer

GET /v1/me/getbalance

[
  {
    "currency_code": "JPY",
    "amount": 1024078,
    "available": 508000
  },
  {
    "currency_code": "BTC",
    "amount": 10.24,
    "available": 4.12
  },
  {
    "currency_code": "ETH",
    "amount": 20.48,
    "available": 16.38
  }
]

## coincheck

GET /api/accounts/balance

{
  "success": true,
  "jpy": "0.8401",
  "btc": "7.75052654",
  "jpy_reserved": "3000.0",
  "btc_reserved": "3.5002",
  "jpy_lend_in_use": "0",
  "btc_lend_in_use": "0.3",
  "jpy_lent": "0",
  "btc_lent": "1.2",
  "jpy_debt": "0",
  "btc_debt": "0"
}

### 補足

jpy 日本円の残高 
btc ビットコインの残高 
jpy_reserved 未決済の買い注文に利用している日本円の合計 
btc_reserved 未決済の売り注文に利用しているビットコインの合計 
jpy_lend_in_use 貸出申請をしている日本円の合計（現在は日本円貸出の機能を提供していません） 
btc_lend_in_use 貸出申請をしているビットコインの合計（現在はビットコイン貸出の機能を提供していません） 
jpy_lent 貸出をしている日本円の合計（現在は日本円貸出の機能を提供していません） 
btc_lent 貸出をしているビットコインの合計（現在はビットコイン貸出の機能を提供していません） 
jpy_debt 借りている日本円の合計 
btc_debt 借りているビットコインの合計 


# 約定履歴 history

## bitflyer

GET /v1/executions

[
  {
    "id": 39287,
    "side": "BUY",
    "price": 31690,
    "size": 27.04,
    "exec_date": "2015-07-08T02:43:34.823",
    "buy_child_order_acceptance_id": "JRF20150707-200203-452209",
    "sell_child_order_acceptance_id": "JRF20150708-024334-060234"
  },
  {
    "id": 39286,
    "side": "SELL",
    "price": 33170,
    "size": 0.36,
    "exec_date": "2015-07-08T02:43:34.72",
    "buy_child_order_acceptance_id": "JRF20150708-010230-400876",
    "sell_child_order_acceptance_id": "JRF20150708-024334-197755"
  }
]

## coincheck

GET /api/trades
- pair: btc_jpy

{
  "success": true,
  "pagination": {
    "limit": 1,
    "order": "desc",
    "starting_after": null,
    "ending_before": null
  },
  "data": [
    {
      "id": 82,
      "amount": "0.28391",
      "rate": 35400,
      "pair": "btc_jpy",
      "order_type": "sell",
      "created_at": "2015-01-10T05:55:38.000Z"
    },
    {
      "id": 81,
      "amount": "0.1",
      "rate": 36120,
      "pair": "btc_jpy",
      "order_type": "buy",
      "created_at": "2015-01-09T15:25:13.000Z"
    }
  ]
}


# Ticker

## bitflyer

GET /v1/ticker

{
  "product_code": "BTC_JPY",
  "timestamp": "2015-07-08T02:50:59.97",
  "tick_id": 3579,
  "best_bid": 30000,
  "best_ask": 36640,
  "best_bid_size": 0.1,
  "best_ask_size": 5,
  "total_bid_depth": 15.13,
  "total_ask_depth": 20,
  "ltp": 31690,
  "volume": 16819.26,
  "volume_by_product": 6819.26
}

## coincheck

GET /api/ticker

{
  "last": 27390,
  "bid": 26900,
  "ask": 27390,
  "high": 27659,
  "low": 26400,
  "volume": "50.29627103",
  "timestamp": 1423377841
}