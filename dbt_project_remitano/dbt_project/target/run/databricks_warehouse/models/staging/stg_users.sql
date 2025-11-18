
  
  
  create or replace view workspace.bronze_bronze.stg_users
  
  as (
    select
    CAST(user_id AS STRING) AS user_id,
    upper(trim(kyc_level)) as kyc_level,
    CAST(created_at AS TIMESTAMP) AS created_at,
    CAST(updated_at AS TIMESTAMP) AS updated_at
from `workspace`.`bronze`.`raw_users`
where user_id is not null
  )
