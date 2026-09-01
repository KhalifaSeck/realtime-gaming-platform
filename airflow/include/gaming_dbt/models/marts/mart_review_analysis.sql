{{ config(materialized='table') }}

{% set lookback_days = var('trending_lookback_days', 30) %}

with games as (
    select * from {{ ref('mart_games') }}
),

stream_reviews as (
    select
        steam_app_id,
        sum(num_reviews)                              as stream_reviews_period,
        avg(avg_rating)                               as stream_avg_rating_period,
        avg(recommend_pct)                            as stream_recommend_pct_period,
        count_if(is_review_bomb)                      as review_bomb_windows_period,
        boolor_agg(is_review_bomb)                    as had_review_bomb_period
    from {{ ref('stg_stream_reviews_agg') }}
    where window_start >= dateadd(day, -{{ lookback_days }}, current_timestamp())
    group by steam_app_id
),

joined as (
    select
        g.steam_app_id,
        g.game_name,
        g.developer,
        g.publisher,
        g.primary_genre_final                                 as primary_genre,
        {{ lookback_days }}                                   as lookback_days,

        g.positive_reviews                                    as historical_positive,
        g.negative_reviews                                    as historical_negative,
        g.review_score                                        as historical_review_score,
        g.review_label                                        as historical_label,

        coalesce(sr.stream_reviews_period, 0)                 as stream_reviews_period,
        sr.stream_avg_rating_period,
        sr.stream_recommend_pct_period,
        coalesce(sr.review_bomb_windows_period, 0)            as review_bomb_windows_period,
        coalesce(sr.had_review_bomb_period, false)            as had_review_bomb_period,

        case
            when sr.stream_recommend_pct_period is null then null
            else round(sr.stream_recommend_pct_period - g.review_score, 2)
        end                                                   as sentiment_drift_pct
    from games g
    left join stream_reviews sr using (steam_app_id)
)

select *
from joined
where stream_reviews_period > 0 or had_review_bomb_period
order by review_bomb_windows_period desc, stream_reviews_period desc