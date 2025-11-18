{{ config(
    materialized='view'
) }}

select
    CAST(user_id AS STRING) AS user_id,
    upper(trim(kyc_level)) as kyc_level,
    CAST(created_at AS TIMESTAMP) AS created_at,
    CAST(updated_at AS TIMESTAMP) AS updated_at
from {{ source('raw','raw_users') }}
where user_id is not null
