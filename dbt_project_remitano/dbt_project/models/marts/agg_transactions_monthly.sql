{{ config(materialized='table') }}

select user_id, 
    count(*) as num_transactions, 
    date_trunc('month', transaction_date) as month,
    sum(amount_usd) as total_amount_usd,
    kyc_level_at_transaction
from {{ ref('fact_transactions') }}
group by user_id, kyc_level_at_transaction, transaction_date