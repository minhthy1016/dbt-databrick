
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select symbol
from workspace.bronze_bronze.stg_transactions
where symbol is null



  
  
      
    ) dbt_internal_test