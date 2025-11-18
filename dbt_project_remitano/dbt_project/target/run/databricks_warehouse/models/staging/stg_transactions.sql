
  
  
  create or replace view workspace.bronze_bronze.stg_transactions
  
  as (
    SELECT
    tx_id as transaction_id,
    customer_id as user_id,
    source_currency,
    destination_currency,
    CAST(source_currency AS FLOAT64) AS source_amount,
    CAST(destination_currency AS FLOAT64) AS destination_currency,
   -- TIMESTAMP(created_at) AS created_at,
    CAST(created_at AS TIMESTAMP) AS created_at,
    UPPER(status) AS status
FROM `workspace`.`bronze`.`raw_transactions`
WHERE tx_id IS NOT NULL
  )
