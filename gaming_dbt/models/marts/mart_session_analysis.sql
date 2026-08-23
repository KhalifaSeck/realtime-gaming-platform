{{ config(materialized='table') }}

{% set lookback_days = var('trending_lookback_days', 30) %}

with games as (
    select * from {{ ref('mart_games') }}
),

stream_sessions as (
    select
        steam_app_id,
        sum(num_starts)                                  as total_starts_period,
        sum(num_ends)                                    as total_ends_period,
        avg(avg_duration_sec)                            as avg_session_duration_sec_period,
        count_if(is_ccu_spike)                           as ccu_spike_windows_period,
        boolor_agg(is_ccu_spike)                         as had_ccu_spike_period,
        max(num_starts)                                  as peak_starts_in_window_period
    from {{ ref('stg_stream_sessions_agg') }}
    where window_start >= dateadd(day, -{{ lookback_days }}, current_timestamp())
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
        {{ lookback_days }}                              as lookback_days,

        coalesce(ss.total_starts_period,        0)       as total_starts_period,
        coalesce(ss.total_ends_period,          0)       as total_ends_period,
        round(ss.avg_session_duration_sec_period / 60.0, 1) as avg_session_duration_min_period,
        coalesce(ss.ccu_spike_windows_period,   0)       as ccu_spike_windows_period,
        coalesce(ss.had_ccu_spike_period,       false)   as had_ccu_spike_period,
        coalesce(ss.peak_starts_in_window_period, 0)     as peak_starts_in_window_period,

        round(
            coalesce(ss.total_ends_period, 0) * 100.0
            / nullif(coalesce(ss.total_starts_period, 0), 0)
        , 2)                                             as completion_rate_pct
    from games g
    left join stream_sessions ss using (steam_app_id)
)

select *
from joined
where total_starts_period > 0 or had_ccu_spike_period
order by peak_starts_in_window_period desc, total_starts_period desc