{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'stream_wishlist') }}
),

cleaned as (
    select
        event_id,
        event_type,
        event_time,
        user_id,
        game_id                                          as steam_app_id,
        action,
        source                                           as wishlist_source,
        date_trunc('hour', event_time)                   as event_hour,
        date_trunc('day',  event_time)                   as event_day,
        _loaded_at                                       as loaded_at
    from source
    where event_id is not null
)

select * from cleaned