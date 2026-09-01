-- Stats par genre : nombre de jeux, market share, positive rate, ranking
{{ config(materialized='table') }}

with games as (
    select * from {{ ref('mart_games') }}
    where primary_genre_final is not null and primary_genre_final <> ''
),

genre_agg as (
    select
        primary_genre_final                              as genre,
        count(*)                                         as num_games,
        sum(owners_estimate)                             as total_owners,
        avg(owners_estimate)                             as avg_owners,
        sum(positive_reviews)                            as total_positive_reviews,
        sum(negative_reviews)                            as total_negative_reviews,
        avg(review_score)                                as avg_review_score,
        avg(price_usd)                                   as avg_price_usd,
        avg(popularity_score)                            as avg_popularity_score
    from games
    group by primary_genre_final
),

totals as (
    select sum(num_games) as total_games from genre_agg
),

final as (
    select
        g.genre,
        g.num_games,
        round(g.num_games * 100.0 / t.total_games, 2)                              as market_share_pct,
        g.total_owners,
        round(g.avg_owners, 0)                                                     as avg_owners,
        g.total_positive_reviews,
        g.total_negative_reviews,
        round(
            g.total_positive_reviews * 100.0
            / nullif(g.total_positive_reviews + g.total_negative_reviews, 0)
        , 2)                                                                       as positive_rate_pct,
        round(g.avg_review_score, 2)                                               as avg_review_score,
        round(g.avg_price_usd, 2)                                                  as avg_price_usd,
        round(g.avg_popularity_score, 2)                                           as avg_popularity_score,
        row_number() over (order by g.total_owners desc)                           as rank_by_owners,
        row_number() over (order by g.num_games desc)                              as rank_by_games
    from genre_agg g
    cross join totals t
)

select * from final
order by rank_by_owners