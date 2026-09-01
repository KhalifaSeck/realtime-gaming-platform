{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'igdb_games') }}
),

renamed as (
    select
        igdb_id                                          as game_id,
        name                                             as game_name,
        summary,
        rating,
        round(rating / 10.0, 2)                          as rating_normalized,
        rating_count,
        release_date,
        genres,
        trim(split_part(genres, ',', 1))                 as primary_genre,
        themes,
        platforms,
        keywords,
        game_modes,
        developer,
        publisher,
        _loaded_at                                       as loaded_at
    from source
    where igdb_id is not null
)

select * from renamed