{{ config(
    materialized='view'
) }}

with tx as (
    select *
    from {{ ref('stg_transactions') }}
),

kyc_hist as (
    -- This is the SCD2 snapshot table
    select
        user_id,
        kyc_level,
        created_at,
        updated_at,
        dbt_valid_from as valid_from,
        dbt_valid_to as valid_to ,
        dbt_updated_at
    from {{ ref('kyc_users') }}
),

fx as (
    select *
    from {{ ref('stg_rates') }}
)

select
    tx.transaction_id,
    tx.user_id,
    tx.source_currency,
    tx.destination_currency,
    tx.source_amount,
    tx.destination_amount,
    fx.close_price as close_rate_to_usd,
    cast(tx.source_amount as float) * fx.close_price as amount_usd,
    tx.status,
    tx.created_at as transaction_date,
    -- KYC LEVEL AT THE TIME OF TRANSACTION
    kyc.kyc_level as kyc_level_at_transaction
from tx
left join kyc_hist kyc
    on tx.user_id = kyc.user_id
    -- This ensures correct historical KYC
    and tx.created_at >= kyc.valid_from
    and (kyc.valid_to is null or tx.created_at < kyc.valid_to)
left join fx
    on tx.source_currency = fx.symbol
    and date(fx.close_time) = date(tx.created_at)
