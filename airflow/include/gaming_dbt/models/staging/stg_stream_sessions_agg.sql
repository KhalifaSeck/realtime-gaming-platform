{{ config(materialized='view') }}

with source as (
    select * from {{ source('analytics', 'stream_sessions_agg') }}
),

enriched as (
    select
        window_start,
        dateadd(second, 30, window_start)                as window_end,
        game_id                                          as steam_app_id,
        num_starts,
        num_ends,
        avg_duration_sec,
        round(avg_duration_sec / 60.0, 1)                as avg_duration_min,
        case when num_starts >= 20 then true else false end as is_ccu_spike,
        _loaded_at                                       as loaded_at
    from source
    where game_id is not null
)

select * from enriched