{% snapshot kyc_users %}
{{ config(
    target_schema='silver',
    unique_key='user_id',
    strategy='timestamp',
    updated_at='updated_at'
) }}

select
  user_id,
  kyc_level,
  created_at,
  updated_at
from {{ ref('stg_users') }}

{% endsnapshot %}

