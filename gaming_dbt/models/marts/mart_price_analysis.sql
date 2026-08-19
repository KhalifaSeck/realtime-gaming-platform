-- Prix vs engagement : par tier, revenue par tier
{{ config(materialized='table') }}

with games as (
    select * from {{ ref('mart_games') }}
),

recent_purchases as (
    select
        steam_app_id,
        sum(num_purchases)      as total_purchases_24h,
        sum(revenue_net_usd)    as total_revenue_24h
    from {{ ref('stg_stream_purchases_agg') }}
    where window_start >= dateadd(hour, -24, current_timestamp())
    group by steam_app_id
),

joined as (
    select
        g.price_tier,
        g.price_usd,
        g.owners_estimate,
        g.review_score,
        g.popularity_score,
        coalesce(rp.total_purchases_24h, 0)              as total_purchases_24h,
        coalesce(rp.total_revenue_24h,   0)              as total_revenue_24h
    from games g
    left join recent_purchases rp using (steam_app_id)
),

tier_agg as (
    select
        price_tier,
        count(*)                                         as num_games,
        round(avg(price_usd), 2)                         as avg_price_usd,
        sum(owners_estimate)                             as total_owners,
        round(avg(owners_estimate), 0)                   as avg_owners,
        round(avg(review_score), 2)                      as avg_review_score,
        round(avg(popularity_score), 2)                  as avg_popularity_score,
        sum(total_purchases_24h)                         as total_purchases_24h,
        round(sum(total_revenue_24h), 2)                 as total_revenue_24h_usd
    from joined
    group by price_tier
),

totals as (
    select sum(total_owners) as owners_all, sum(total_revenue_24h_usd) as revenue_all
    from tier_agg
)

select
    t.price_tier,
    t.num_games,
    t.avg_price_usd,
    t.total_owners,
    t.avg_owners,
    round(t.total_owners * 100.0 / nullif(tot.owners_all, 0), 2)          as owners_share_pct,
    t.avg_review_score,
    t.avg_popularity_score,
    t.total_purchases_24h,
    t.total_revenue_24h_usd,
    round(t.total_revenue_24h_usd * 100.0 / nullif(tot.revenue_all, 0), 2) as revenue_share_pct_24h
from tier_agg t
cross join totals tot
order by t.avg_popularity_score desc nulls last