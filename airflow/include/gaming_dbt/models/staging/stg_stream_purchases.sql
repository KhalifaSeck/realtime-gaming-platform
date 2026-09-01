{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'stream_purchases') }}
),

cleaned as (
    select
        event_id,
        event_type,
        event_time,
        user_id,
        game_id                                          as steam_app_id,
        price_usd,
        discount_pct,
        payment_method,
        country,
        round(price_usd * (1 - discount_pct / 100.0), 2) as revenue_net_usd,
        date_trunc('hour', event_time)                   as event_hour,
        date_trunc('day',  event_time)                   as event_day,
        _loaded_at                                       as loaded_at
    from source
    where event_id is not null and game_id is not null
)

select * from cleaned