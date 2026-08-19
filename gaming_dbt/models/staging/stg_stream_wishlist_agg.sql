{{ config(materialized='view') }}

with source as (
    select * from {{ source('analytics', 'stream_wishlist_agg') }}
),

enriched as (
    select
        window_start,
        dateadd(second, 30, window_start)                as window_end,
        game_id                                          as steam_app_id,
        num_added,
        num_removed,
        net_added,
        case when net_added >= 15 then true else false end as is_viral_wishlist,
        _loaded_at                                       as loaded_at
    from source
    where game_id is not null
)

select * from enriched