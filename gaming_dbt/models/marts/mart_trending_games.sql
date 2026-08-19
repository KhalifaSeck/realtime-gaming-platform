{{ config(materialized='table') }}

with recent_purchases as (
    select
        steam_app_id,
        sum(num_purchases)                            as total_purchases_24h,
        sum(revenue_net_usd)                          as total_revenue_24h_usd,
        boolor_agg(is_viral)                          as had_viral_purchases_24h
    from {{ ref('stg_stream_purchases_agg') }}
    where window_start >= dateadd(hour, -24, current_timestamp())
    group by steam_app_id
),

recent_reviews as (
    select
        steam_app_id,
        sum(num_reviews)                              as total_reviews_24h,
        avg(avg_rating)                               as avg_rating_24h,
        avg(recommend_pct)                            as recommend_pct_24h,
        boolor_agg(is_review_bomb)                    as had_review_bomb_24h
    from {{ ref('stg_stream_reviews_agg') }}
    where window_start >= dateadd(hour, -24, current_timestamp())
    group by steam_app_id
),

recent_sessions as (
    select
        steam_app_id,
        sum(num_starts)                               as total_sessions_24h,
        avg(avg_duration_sec)                         as avg_session_duration_sec_24h,
        boolor_agg(is_ccu_spike)                      as had_ccu_spike_24h
    from {{ ref('stg_stream_sessions_agg') }}
    where window_start >= dateadd(hour, -24, current_timestamp())
    group by steam_app_id
),

recent_wishlist as (
    select
        steam_app_id,
        sum(num_added)                                as wishlist_added_24h,
        sum(num_removed)                              as wishlist_removed_24h,
        sum(net_added)                                as wishlist_net_added_24h,
        boolor_agg(is_viral_wishlist)                 as had_viral_wishlist_24h
    from {{ ref('stg_stream_wishlist_agg') }}
    where window_start >= dateadd(hour, -24, current_timestamp())
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
        coalesce(p.total_purchases_24h,   0)          as total_purchases_24h,
        coalesce(p.total_revenue_24h_usd, 0)          as total_revenue_24h_usd,
        coalesce(r.total_reviews_24h,     0)          as total_reviews_24h,
        r.avg_rating_24h,
        r.recommend_pct_24h,
        coalesce(s.total_sessions_24h,    0)          as total_sessions_24h,
        s.avg_session_duration_sec_24h,
        coalesce(w.wishlist_net_added_24h, 0)         as wishlist_net_added_24h,
        coalesce(p.had_viral_purchases_24h,  false)   as had_viral_purchases_24h,
        coalesce(r.had_review_bomb_24h,      false)   as had_review_bomb_24h,
        coalesce(s.had_ccu_spike_24h,        false)   as had_ccu_spike_24h,
        coalesce(w.had_viral_wishlist_24h,   false)   as had_viral_wishlist_24h,
        (
              coalesce(p.total_purchases_24h,     0) * 5
            + coalesce(r.total_reviews_24h,       0) * 3
            + coalesce(s.total_sessions_24h,      0) * 1
            + coalesce(w.wishlist_net_added_24h,  0) * 2
        )                                             as trending_score
    from games g
    left join recent_purchases p using (steam_app_id)
    left join recent_reviews   r using (steam_app_id)
    left join recent_sessions  s using (steam_app_id)
    left join recent_wishlist  w using (steam_app_id)
    where coalesce(p.total_purchases_24h, 0)
        + coalesce(r.total_reviews_24h, 0)
        + coalesce(s.total_sessions_24h, 0)
        + abs(coalesce(w.wishlist_net_added_24h, 0)) > 0
)

select * from trending
order by trending_score desc