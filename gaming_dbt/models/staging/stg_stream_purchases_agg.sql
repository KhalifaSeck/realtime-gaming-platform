{{ config(materialized='view') }}

with source as (
    select * from {{ source('analytics', 'stream_purchases_agg') }}
),

enriched as (
    select
        window_start,
        dateadd(second, 30, window_start)                as window_end,
        game_id                                          as steam_app_id,
        num_purchases,
        revenue_net_usd,
        round(revenue_net_usd / nullif(num_purchases, 0), 2) as avg_price_per_purchase,
        case when num_purchases >= 15 then true else false end as is_viral,
        _loaded_at                                       as loaded_at
    from source
    where game_id is not null
)

select * from enriched