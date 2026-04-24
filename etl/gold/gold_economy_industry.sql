-- Gold industry structure mart
-- Grain: one row per geo_level + geo_id + year.
-- Uses ACS as the geography spine so all ACS-supported geographies are present.
-- BEA industry GDP fields are left-joined and sparse outside BEA-supported grains.

create or replace table metro_deep_dive.gold.economics_industry_wide as
with acs_base as (
    select
        lower(geo_level) as geo_level,
        geo_id,
        geo_name,
        year,
        pop_total
    from metro_deep_dive.silver.age_kpi
),

acs_industry as (
    select
        lower(geo_level) as geo_level,
        geo_id,
        geo_name,
        year,
        ind_total_emp as acs_ind_total_emp,
        ind_ag_mining as acs_ind_ag_mining,
        ind_construction as acs_ind_construction,
        ind_manufacturing as acs_ind_manufacturing,
        ind_wholesale as acs_ind_wholesale,
        ind_retail as acs_ind_retail,
        ind_transport_util as acs_ind_transport_util,
        ind_information as acs_ind_information,
        ind_finance_real as acs_ind_finance_real,
        ind_professional as acs_ind_professional,
        ind_educ_health as acs_ind_educ_health,
        ind_arts_accomm_food as acs_ind_arts_accomm_food,
        ind_other_services as acs_ind_other_services,
        ind_public_admin as acs_ind_public_admin,
        pct_ind_ag_mining as pct_acs_ind_ag_mining,
        pct_ind_construction as pct_acs_ind_construction,
        pct_ind_manufacturing as pct_acs_ind_manufacturing,
        pct_ind_wholesale as pct_acs_ind_wholesale,
        pct_ind_retail as pct_acs_ind_retail,
        pct_ind_transport_util as pct_acs_ind_transport_util,
        pct_ind_information as pct_acs_ind_information,
        pct_ind_finance_real as pct_acs_ind_finance_real,
        pct_ind_professional as pct_acs_ind_professional,
        pct_ind_educ_health as pct_acs_ind_educ_health,
        pct_ind_arts_accomm_food as pct_acs_ind_arts_accomm_food,
        pct_ind_other_services as pct_acs_ind_other_services,
        pct_ind_public_admin as pct_acs_ind_public_admin
    from metro_deep_dive.silver.labor_kpi
),

bea_industry as (
    select
        case
            when geo_id = '00000' then 'us'
            else lower(geo_level)
        end as geo_level,
        case
            when geo_id = '00000' then '1'
            when lower(geo_level) = 'state'
                and length(geo_id) = 5
                and substr(geo_id, 3, 3) = '000'
                then substr(geo_id, 1, 2)
            else geo_id
        end as geo_id,
        geo_name,
        period as year,
        real_gdp_total,
        real_gdp_natural_resources_all as real_gdp_natural_resources,
        real_gdp_manufacturing_all as real_gdp_manufacturing,
        real_gdp_construction,
        real_gdp_trade_all as real_gdp_trade,
        real_gdp_transportation,
        real_gdp_information,
        real_gdp_finance_insurance + real_gdp_real_estate as real_gdp_fire,
        real_gdp_professional_scientific
            + real_gdp_professional_management
            + real_gdp_professional_admin_support as real_gdp_professional,
        real_gdp_education_all as real_gdp_edu_health,
        real_gdp_arts_entertainment + real_gdp_accomodation_food as real_gdp_leisure,
        real_gdp_gov_enterprises as real_gdp_gov,
        real_gdp_natural_resources_all / nullif(real_gdp_total, 0) as pct_real_gdp_natural_resources,
        real_gdp_manufacturing_all / nullif(real_gdp_total, 0) as pct_real_gdp_manufacturing,
        real_gdp_construction / nullif(real_gdp_total, 0) as pct_real_gdp_construction,
        real_gdp_trade_all / nullif(real_gdp_total, 0) as pct_real_gdp_trade,
        real_gdp_transportation / nullif(real_gdp_total, 0) as pct_real_gdp_transportation,
        real_gdp_information / nullif(real_gdp_total, 0) as pct_real_gdp_information,
        (real_gdp_finance_insurance + real_gdp_real_estate) / nullif(real_gdp_total, 0) as pct_real_gdp_fire,
        (real_gdp_professional_scientific
            + real_gdp_professional_management
            + real_gdp_professional_admin_support) / nullif(real_gdp_total, 0) as pct_real_gdp_professional,
        real_gdp_education_all / nullif(real_gdp_total, 0) as pct_real_gdp_edu_health,
        (real_gdp_arts_entertainment + real_gdp_accomodation_food) / nullif(real_gdp_total, 0) as pct_real_gdp_leisure,
        real_gdp_gov_enterprises / nullif(real_gdp_total, 0) as pct_real_gdp_gov
    from metro_deep_dive.silver.bea_regional_cagdp9_wide
),

final as (
    select
        b.geo_level,
        b.geo_id,
        coalesce(b.geo_name, a.geo_name, bea.geo_name) as geo_name,
        b.year,
        b.pop_total,
        a.acs_ind_total_emp,
        a.acs_ind_ag_mining,
        a.acs_ind_construction,
        a.acs_ind_manufacturing,
        a.acs_ind_wholesale,
        a.acs_ind_retail,
        a.acs_ind_transport_util,
        a.acs_ind_information,
        a.acs_ind_finance_real,
        a.acs_ind_professional,
        a.acs_ind_educ_health,
        a.acs_ind_arts_accomm_food,
        a.acs_ind_other_services,
        a.acs_ind_public_admin,
        a.pct_acs_ind_ag_mining,
        a.pct_acs_ind_construction,
        a.pct_acs_ind_manufacturing,
        a.pct_acs_ind_wholesale,
        a.pct_acs_ind_retail,
        a.pct_acs_ind_transport_util,
        a.pct_acs_ind_information,
        a.pct_acs_ind_finance_real,
        a.pct_acs_ind_professional,
        a.pct_acs_ind_educ_health,
        a.pct_acs_ind_arts_accomm_food,
        a.pct_acs_ind_other_services,
        a.pct_acs_ind_public_admin,
        bea.real_gdp_total,
        bea.real_gdp_natural_resources,
        bea.real_gdp_manufacturing,
        bea.real_gdp_construction,
        bea.real_gdp_trade,
        bea.real_gdp_transportation,
        bea.real_gdp_information,
        bea.real_gdp_fire,
        bea.real_gdp_professional,
        bea.real_gdp_edu_health,
        bea.real_gdp_leisure,
        bea.real_gdp_gov,
        bea.pct_real_gdp_natural_resources,
        bea.pct_real_gdp_manufacturing,
        bea.pct_real_gdp_construction,
        bea.pct_real_gdp_trade,
        bea.pct_real_gdp_transportation,
        bea.pct_real_gdp_information,
        bea.pct_real_gdp_fire,
        bea.pct_real_gdp_professional,
        bea.pct_real_gdp_edu_health,
        bea.pct_real_gdp_leisure,
        bea.pct_real_gdp_gov
    from acs_base b
    left join acs_industry a
        on b.geo_level = a.geo_level
       and b.geo_id = a.geo_id
       and b.year = a.year
    left join bea_industry bea
        on b.geo_level = bea.geo_level
       and b.geo_id = bea.geo_id
       and b.year = bea.year
)

select
    *,
    real_gdp_natural_resources
        + real_gdp_manufacturing
        + real_gdp_construction
        + real_gdp_trade
        + real_gdp_transportation
        + real_gdp_information
        + real_gdp_fire
        + real_gdp_professional
        + real_gdp_edu_health
        + real_gdp_leisure
        + real_gdp_gov as sector_sum,
    real_gdp_total - sector_sum as calc_real_gdp_other,
    calc_real_gdp_other / nullif(real_gdp_total, 0) as pct_calc_real_gdp_other,
    (
        power(pct_real_gdp_natural_resources, 2)
        + power(pct_real_gdp_manufacturing, 2)
        + power(pct_real_gdp_construction, 2)
        + power(pct_real_gdp_trade, 2)
        + power(pct_real_gdp_transportation, 2)
        + power(pct_real_gdp_information, 2)
        + power(pct_real_gdp_fire, 2)
        + power(pct_real_gdp_professional, 2)
        + power(pct_real_gdp_edu_health, 2)
        + power(pct_real_gdp_leisure, 2)
        + power(pct_real_gdp_gov, 2)
        + power(pct_calc_real_gdp_other, 2)
    ) as industry_concentration_hhi,
    (
        power(pct_acs_ind_ag_mining, 2)
        + power(pct_acs_ind_construction, 2)
        + power(pct_acs_ind_manufacturing, 2)
        + power(pct_acs_ind_wholesale, 2)
        + power(pct_acs_ind_retail, 2)
        + power(pct_acs_ind_transport_util, 2)
        + power(pct_acs_ind_information, 2)
        + power(pct_acs_ind_finance_real, 2)
        + power(pct_acs_ind_professional, 2)
        + power(pct_acs_ind_educ_health, 2)
        + power(pct_acs_ind_arts_accomm_food, 2)
        + power(pct_acs_ind_other_services, 2)
        + power(pct_acs_ind_public_admin, 2)
    ) as acs_industry_concentration_hhi,
    sector_sum / nullif(real_gdp_total, 0) as sector_sum_ratio,
    case
        when sector_sum_ratio > 1.05 then 'Sector Bug'
        when sector_sum_ratio is null then null
        else 'Non Bug'
    end as sector_sum_ratio_quality_flag
from final;
