{{ config(materialized='view') }}

with source as (
    select * from {{ source('analytics', 'stream_reviews_agg') }}
),

enriched as (
    select
        window_start,
        dateadd(second, 30, window_start)                as window_end,
        game_id                                          as steam_app_id,
        num_reviews,
        avg_rating,
        recommend_pct,
        case
            when num_reviews >= 10 and avg_rating    < 4  then true
            when num_reviews >= 5  and recommend_pct < 30 then true
            else false
        end                                              as is_review_bomb,
        _loaded_at                                       as loaded_at
    from source
    where game_id is not null
)

select * from enriched