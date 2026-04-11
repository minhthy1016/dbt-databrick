{{ config(
    materialized='table'
) }}

select
    transaction_id,
    user_id,
    CAST(source_amount AS FLOAT) AS source_amount,
    CAST(destination_amount AS FLOAT) AS destination_amount,
    CAST(source_currency AS STRING) AS source_currency, 
    destination_currency,
    CAST(close_rate_to_usd AS FLOAT) AS close_rate_to_usd, 
    CAST(amount_usd AS FLOAT) AS amount_usd,
    status,
    transaction_date,
    kyc_level_at_transaction
from {{ ref('int_transactions_enriched') }}
where status = 'completed'
