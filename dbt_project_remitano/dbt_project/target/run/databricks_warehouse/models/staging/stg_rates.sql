
  
  
  create or replace view workspace.bronze_bronze.stg_rates
  
  as (
    SELECT
    symbol,
    CAST(open_time AS TIMESTAMP) AS open_time,
    CAST(close_time AS TIMESTAMP) AS close_time,
    CAST(open AS FLOAT64) AS open_price,
    CAST(close AS FLOAT64) AS close_price,
    CAST(volume AS FLOAT64) AS volume,
    CAST(quote_asset_volume AS FLOAT64) AS quote_volume, 
    CAST(num_trades AS FLOAT64) AS num_trades,
    CAST(taker_buy_base AS FLOAT64) AS taker_buy_base,
    CAST(taker_buy_quote AS FLOAT64) AS taker_buy_quote    
FROM `workspace`.`bronze`.`raw_rates`
WHERE symbol IS NOT NULL 
AND close_price IS NOT NULL
  )
