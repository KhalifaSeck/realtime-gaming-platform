{{ config(materialized='table') }}

with games as (
    select * from {{ ref('mart_games') }}
),

stream_reviews as (
    select
        steam_app_id,
        sum(num_reviews)                              as stream_reviews_24h,
        avg(avg_rating)                               as stream_avg_rating_24h,
        avg(recommend_pct)                            as stream_recommend_pct_24h,
        count_if(is_review_bomb)                      as review_bomb_windows_24h,
        boolor_agg(is_review_bomb)                    as had_review_bomb_24h
    from {{ ref('stg_stream_reviews_agg') }}
    where window_start >= dateadd(hour, -24, current_timestamp())
    group by steam_app_id
),

joined as (
    select
        g.steam_app_id,
        g.game_name,
        g.developer,
        g.publisher,
        g.primary_genre_final                                 as primary_genre,

        g.positive_reviews                                    as historical_positive,
        g.negative_reviews                                    as historical_negative,
        g.review_score                                        as historical_review_score,
        g.review_label                                        as historical_label,

        coalesce(sr.stream_reviews_24h, 0)                    as stream_reviews_24h,
        sr.stream_avg_rating_24h,
        sr.stream_recommend_pct_24h,
        coalesce(sr.review_bomb_windows_24h, 0)               as review_bomb_windows_24h,
        coalesce(sr.had_review_bomb_24h, false)               as had_review_bomb_24h,

        case
            when sr.stream_recommend_pct_24h is null then null
            else round(sr.stream_recommend_pct_24h - g.review_score, 2)
        end                                                   as sentiment_drift_pct
    from games g
    left join stream_reviews sr using (steam_app_id)
)

select *
from joined
where stream_reviews_24h > 0 or had_review_bomb_24h
order by review_bomb_windows_24h desc, stream_reviews_24h desc