{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'steamspy_games') }}
),

renamed as (
    select
        appid                                            as steam_app_id,
        name                                             as game_name,
        developer,
        publisher,
        owners_range,
        owners_estimate,
        ccu                                              as concurrent_users,
        price_usd,
        initialprice_usd                                 as initial_price_usd,
        discount_pct,
        positive                                         as positive_reviews,
        negative                                         as negative_reviews,
        review_score,
        round(average_forever / 60.0, 1)                 as avg_playtime_hours,
        round(average_2weeks  / 60.0, 1)                 as avg_playtime_2weeks_hours,
        round(median_forever  / 60.0, 1)                 as median_playtime_hours,
        case
            when price_usd = 0                          then 'free'
            when price_usd between 0.01 and 9.99        then 'cheap'
            when price_usd between 10.00 and 29.99      then 'medium'
            when price_usd between 30.00 and 59.99      then 'premium'
            when price_usd > 60                         then 'aaa'
            else 'unknown'
        end                                              as price_tier,
        case
            when review_score is null                                          then 'no_reviews'
            when review_score >= 95 and (positive + negative) >= 500           then 'overwhelmingly_positive'
            when review_score >= 85                                            then 'very_positive'
            when review_score >= 70                                            then 'mostly_positive'
            when review_score >= 40                                            then 'mixed'
            when review_score >= 20                                            then 'mostly_negative'
            else 'very_negative'
        end                                              as review_label,
        tags,
        languages,
        genre                                            as steam_genre,
        _loaded_at                                       as loaded_at
    from source
    where appid is not null
)

select * from renamed