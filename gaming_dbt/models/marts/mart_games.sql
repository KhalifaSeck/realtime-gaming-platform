-- Table maitre : IGDB + SteamSpy joints, popularity_score + tiers
{{ config(materialized='table') }}

with steam as (
    select * from {{ ref('stg_steamspy_games') }}
),

igdb as (
    select * from {{ ref('stg_igdb_games') }}
),

joined as (
    select
        s.steam_app_id,
        s.game_name,
        s.developer                                       as steam_developer,
        s.publisher                                       as steam_publisher,
        s.owners_estimate,
        s.owners_range,
        s.concurrent_users,
        s.price_usd,
        s.initial_price_usd,
        s.discount_pct,
        s.price_tier,
        s.positive_reviews,
        s.negative_reviews,
        s.review_score,
        s.review_label,
        s.avg_playtime_hours,
        s.avg_playtime_2weeks_hours,
        s.median_playtime_hours,
        s.tags,
        s.languages,
        s.steam_genre,
        i.game_id                                         as igdb_id,
        i.summary                                         as igdb_summary,
        i.rating                                          as igdb_rating,
        i.rating_normalized                               as igdb_rating_norm,
        i.rating_count                                    as igdb_rating_count,
        i.release_date,
        i.genres                                          as igdb_genres,
        i.primary_genre,
        i.themes,
        i.platforms,
        i.keywords,
        i.game_modes,
        i.developer                                       as igdb_developer,
        i.publisher                                       as igdb_publisher,
        coalesce(nullif(i.developer, ''), s.developer)    as developer,
        coalesce(nullif(i.publisher, ''), s.publisher)    as publisher,
        coalesce(nullif(i.primary_genre, ''), s.steam_genre) as primary_genre_final
    from steam s
    left join igdb i
      on lower(trim(s.game_name)) = lower(trim(i.game_name))
),

scored as (
    select
        *,
        round(
            (case when owners_estimate > 0 then ln(owners_estimate) else 0 end) * 5
            + coalesce(review_score, 0) * 0.3
            + case when concurrent_users > 0 then ln(concurrent_users) else 0 end * 2
        , 2)                                              as popularity_score
    from joined
),

tiered as (
    select
        *,
        case
            when popularity_score >= 100 then 'superstar'
            when popularity_score >= 70  then 'hit'
            when popularity_score >= 40  then 'mid'
            when popularity_score >= 10  then 'niche'
            else 'unknown'
        end                                               as popularity_tier
    from scored
)

select * from tiered