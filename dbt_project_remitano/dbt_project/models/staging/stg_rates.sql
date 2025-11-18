
{{ config(materialized='view') }}

SELECT
    symbol,
    CAST(open_time AS TIMESTAMP) AS open_time,
    CAST(close_time AS TIMESTAMP) AS close_time,
    CAST(open AS FLOAT) AS open_price,
    CAST(close AS FLOAT) AS close_price,
    CAST(volume AS FLOAT) AS volume,
    CAST(quote_asset_volume AS FLOAT) AS quote_volume, 
    CAST(num_trades AS FLOAT) AS num_trades,
    CAST(taker_buy_base AS FLOAT) AS taker_buy_base,
    CAST(taker_buy_quote AS FLOAT) AS taker_buy_quote    
FROM {{ source('raw', 'combine_raw_rates') }}
WHERE symbol IS NOT NULL 
AND close IS NOT NULL
