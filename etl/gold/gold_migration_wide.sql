-- Gold migration mart
-- Grain: one row per geo_level + geo_id + year
-- First pass is ACS-only by design; IRS flow fields are left as explicit null placeholders.

create or replace table metro_deep_dive.gold.migration_wide as
with migration as (
    select
        lower(geo_level) as geo_level,
        geo_id,
        geo_name,
        year,
        mig_total,
        mig_same_house,
        mig_moved_same_cnty,
        mig_moved_same_st,
        mig_moved_diff_st,
        mig_moved_abroad,
        pct_same_house,
        pct_moved_same_cnty,
        pct_moved_same_st,
        pct_moved_diff_st,
        pct_moved_abroad,
        pop_nativity_total,
        pop_native,
        pop_foreign_born,
        pop_foreign_born_citizen,
        pop_foreign_born_noncitizen,
        pct_native,
        pct_foreign_born,
        pct_non_citizen
    from metro_deep_dive.silver.migration_kpi
)

select
    geo_level,
    geo_id,
    geo_name,
    year,
    mig_total,
    mig_same_house,
    mig_moved_same_cnty,
    mig_moved_same_st,
    mig_moved_diff_st,
    mig_moved_abroad,
    pct_same_house,
    pct_moved_same_cnty,
    pct_moved_same_st,
    pct_moved_diff_st,
    pct_moved_abroad,
    case
        when pct_same_house is not null then 1.0 - pct_same_house
        else null
    end as mobility_rate,
    coalesce(pct_moved_same_cnty, 0)
        + coalesce(pct_moved_same_st, 0)
        + coalesce(pct_moved_diff_st, 0) as pct_moved_domestic,
    coalesce(pct_moved_same_cnty, 0)
        + coalesce(pct_moved_same_st, 0)
        + coalesce(pct_moved_diff_st, 0)
        + coalesce(pct_moved_abroad, 0) as migration_churn,
    coalesce(mig_moved_same_cnty, 0)
        + coalesce(mig_moved_same_st, 0)
        + coalesce(mig_moved_diff_st, 0)
        + coalesce(mig_moved_abroad, 0) as migration_churn_count,
    pop_nativity_total,
    pop_native,
    pop_foreign_born,
    pop_foreign_born_citizen,
    pop_foreign_born_noncitizen,
    pct_native,
    pct_foreign_born,
    pct_non_citizen,
    case
        when pop_nativity_total > 0
            then pop_foreign_born_citizen / pop_nativity_total
        else null
    end as pct_foreign_born_citizen,
    case
        when pop_nativity_total > 0
            then pop_foreign_born_noncitizen / pop_nativity_total
        else null
    end as pct_foreign_born_noncitizen,
    cast(null as double) as irs_inflow_total,
    cast(null as double) as irs_outflow_total,
    cast(null as double) as irs_net_migration,
    cast(null as double) as irs_net_migration_rate,
    cast(null as double) as irs_migration_churn
from migration
;
