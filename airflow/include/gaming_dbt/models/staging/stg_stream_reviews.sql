{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'stream_reviews') }}
),

cleaned as (
    select
        event_id,
        event_type,
        event_time,
        user_id,
        game_id                                          as steam_app_id,
        rating,
        recommended,
        hours_played,
        review_length_chars,
        language,
        helpful_votes,
        date_trunc('hour', event_time)                   as event_hour,
        date_trunc('day',  event_time)                   as event_day,
        _loaded_at                                       as loaded_at
    from source
    where event_id is not null and game_id is not null
)

select * from cleaned