-- Batch + streaming + anomaly flags sur la fenetre var('trending_lookback_days')
{{ config(materialized='table') }}

{% set lookback_days = var('trending_lookback_days', 30) %}

with recent_purchases as (
    select
        steam_app_id,
        sum(num_purchases)                            as total_purchases_period,
        sum(revenue_net_usd)                          as total_revenue_period_usd,
        boolor_agg(is_viral)                          as had_viral_purchases_period
    from {{ ref('stg_stream_purchases_agg') }}
    where window_start >= dateadd(day, -{{ lookback_days }}, current_timestamp())
    group by steam_app_id
),

recent_reviews as (
    select
        steam_app_id,
        sum(num_reviews)                              as total_reviews_period,
        avg(avg_rating)                               as avg_rating_period,
        avg(recommend_pct)                            as recommend_pct_period,
        boolor_agg(is_review_bomb)                    as had_review_bomb_period
    from {{ ref('stg_stream_reviews_agg') }}
    where window_start >= dateadd(day, -{{ lookback_days }}, current_timestamp())
    group by steam_app_id
),

recent_sessions as (
    select
        steam_app_id,
        sum(num_starts)                               as total_sessions_period,
        avg(avg_duration_sec)                         as avg_session_duration_sec_period,
        boolor_agg(is_ccu_spike)                      as had_ccu_spike_period
    from {{ ref('stg_stream_sessions_agg') }}
    where window_start >= dateadd(day, -{{ lookback_days }}, current_timestamp())
    group by steam_app_id
),

recent_wishlist as (
    select
        steam_app_id,
        sum(num_added)                                as wishlist_added_period,
        sum(num_removed)                              as wishlist_removed_period,
        sum(net_added)                                as wishlist_net_added_period,
        boolor_agg(is_viral_wishlist)                 as had_viral_wishlist_period
    from {{ ref('stg_stream_wishlist_agg') }}
    where window_start >= dateadd(day, -{{ lookback_days }}, current_timestamp())
    group by steam_app_id
),

games as (
    select * from {{ ref('mart_games') }}
),

trending as (
    select
        g.steam_app_id,
        g.game_name,
        g.developer,
        g.publisher,
        g.primary_genre_final                         as primary_genre,
        g.owners_estimate,
        g.popularity_score,
        g.popularity_tier,
        {{ lookback_days }}                           as lookback_days,

        coalesce(p.total_purchases_period,   0)       as total_purchases_period,
        coalesce(p.total_revenue_period_usd, 0)       as total_revenue_period_usd,
        coalesce(r.total_reviews_period,     0)       as total_reviews_period,
        r.avg_rating_period,
        r.recommend_pct_period,
        coalesce(s.total_sessions_period,    0)       as total_sessions_period,
        s.avg_session_duration_sec_period,
        coalesce(w.wishlist_net_added_period, 0)      as wishlist_net_added_period,
        coalesce(p.had_viral_purchases_period,  false) as had_viral_purchases_period,
        coalesce(r.had_review_bomb_period,      false) as had_review_bomb_period,
        coalesce(s.had_ccu_spike_period,        false) as had_ccu_spike_period,
        coalesce(w.had_viral_wishlist_period,   false) as had_viral_wishlist_period,

        (
              coalesce(p.total_purchases_period,     0) * 5
            + coalesce(r.total_reviews_period,       0) * 3
            + coalesce(s.total_sessions_period,      0) * 1
            + coalesce(w.wishlist_net_added_period,  0) * 2
        )                                             as trending_score
    from games g
    left join recent_purchases p using (steam_app_id)
    left join recent_reviews   r using (steam_app_id)
    left join recent_sessions  s using (steam_app_id)
    left join recent_wishlist  w using (steam_app_id)
    where coalesce(p.total_purchases_period, 0)
        + coalesce(r.total_reviews_period, 0)
        + coalesce(s.total_sessions_period, 0)
        + abs(coalesce(w.wishlist_net_added_period, 0)) > 0
)

select * from trending
order by trending_score desc