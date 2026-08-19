{{ config(materialized='table') }}

with games as (
    select * from {{ ref('mart_games') }}
),

stream_sessions as (
    select
        steam_app_id,
        sum(num_starts)                                  as total_starts_24h,
        sum(num_ends)                                    as total_ends_24h,
        avg(avg_duration_sec)                            as avg_session_duration_sec_24h,
        count_if(is_ccu_spike)                           as ccu_spike_windows_24h,
        boolor_agg(is_ccu_spike)                         as had_ccu_spike_24h,
        max(num_starts)                                  as peak_starts_in_window_24h
    from {{ ref('stg_stream_sessions_agg') }}
    where window_start >= dateadd(hour, -24, current_timestamp())
    group by steam_app_id
),

joined as (
    select
        g.steam_app_id,
        g.game_name,
        g.developer,
        g.primary_genre_final                            as primary_genre,
        g.owners_estimate,
        g.concurrent_users                               as steam_concurrent_users,
        g.avg_playtime_hours                             as historical_avg_playtime_hours,

        coalesce(ss.total_starts_24h,        0)          as total_starts_24h,
        coalesce(ss.total_ends_24h,          0)          as total_ends_24h,
        round(ss.avg_session_duration_sec_24h / 60.0, 1) as avg_session_duration_min_24h,
        coalesce(ss.ccu_spike_windows_24h,   0)          as ccu_spike_windows_24h,
        coalesce(ss.had_ccu_spike_24h,       false)      as had_ccu_spike_24h,
        coalesce(ss.peak_starts_in_window_24h, 0)        as peak_starts_in_window_24h,

        round(
            coalesce(ss.total_ends_24h, 0) * 100.0
            / nullif(coalesce(ss.total_starts_24h, 0), 0)
        , 2)                                             as completion_rate_pct
    from games g
    left join stream_sessions ss using (steam_app_id)
)

select *
from joined
where total_starts_24h > 0 or had_ccu_spike_24h
order by peak_starts_in_window_24h desc, total_starts_24h desc