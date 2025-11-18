
{{ config(materialized='view') }}

SELECT
    txn_id as transaction_id,
    user_id,
    source_currency,
    destination_currency, 
    CAST(source_amount AS FLOAT) AS source_amount,
    CAST(destination_amount AS FLOAT) AS destination_amount,
   -- TIMESTAMP(created_at) AS created_at,
    CAST(created_at AS TIMESTAMP) AS created_at,
    status
FROM {{ source('raw', 'raw_transactions') }}
WHERE txn_id IS NOT NULL 
