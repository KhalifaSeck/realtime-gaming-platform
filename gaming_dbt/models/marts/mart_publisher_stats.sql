-- Ranking publishers : market share, genres couverts
{{ config(materialized='table') }}

with games as (
    select * from {{ ref('mart_games') }}
    where publisher is not null and publisher <> ''
),

pub_agg as (
    select
        publisher,
        count(*)                                         as num_games,
        count(distinct primary_genre_final)              as num_distinct_genres,
        sum(owners_estimate)                             as total_owners,
        avg(owners_estimate)                             as avg_owners,
        sum(positive_reviews)                            as total_positive_reviews,
        sum(negative_reviews)                            as total_negative_reviews,
        avg(review_score)                                as avg_review_score,
        avg(price_usd)                                   as avg_price_usd,
        avg(popularity_score)                            as avg_popularity_score
    from games
    group by publisher
),

totals as (
    select sum(num_games) as total_games, sum(total_owners) as total_owners_all
    from pub_agg
),

final as (
    select
        p.publisher,
        p.num_games,
        p.num_distinct_genres,
        round(p.num_games * 100.0 / t.total_games, 2)                              as market_share_games_pct,
        p.total_owners,
        round(p.total_owners * 100.0 / nullif(t.total_owners_all, 0), 2)           as market_share_owners_pct,
        round(p.avg_owners, 0)                                                     as avg_owners,
        round(
            p.total_positive_reviews * 100.0
            / nullif(p.total_positive_reviews + p.total_negative_reviews, 0)
        , 2)                                                                       as positive_rate_pct,
        round(p.avg_review_score, 2)                                               as avg_review_score,
        round(p.avg_price_usd, 2)                                                  as avg_price_usd,
        round(p.avg_popularity_score, 2)                                           as avg_popularity_score,
        row_number() over (order by p.total_owners desc)                           as rank_by_owners,
        row_number() over (order by p.num_games desc)                              as rank_by_games
    from pub_agg p
    cross join totals t
)

select * from final
order by rank_by_owners