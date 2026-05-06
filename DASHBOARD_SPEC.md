# Data Explorer Dashboard — Specification

**Purpose:** A Streamlit reference tool that lets users look up ground-truth values from the Gold data layer and manually compare them to chatbot outputs. Not a chatbot replacement — a QA lens on the underlying data.

**File:** `reference_dashboard/data_explorer.py`

---

## Overall Layout

```
┌──────────────────────────────────────────────────────────────────────────┐
│  SIDEBAR (270 px)         │  MAIN CONTENT                                │
│                           │                                              │
│  [Geo Level]              │  ┌──────────────────────────────────────────┐│
│  [State Filter]           │  │  CHOROPLETH MAP (full width, ~420px tall) ││
│  ─────────────────        │  │  colored by single selected KPI           ││
│  [Subject Area]           │  └──────────────────────────────────────────┘│
│  [Map KPI]                │                                              │
│  [Table KPIs]             │  ┌──────────────────────────────────────────┐│
│  ─────────────────        │  │  DATA TABLE (scrollable)                  ││
│  [Year]                   │  │  geo_name + all selected table KPIs       ││
│  [KPI Range Slider]       │  │  + growth metrics columns                 ││
│                           │  │  filtered by KPI range slider             ││
│                           │  └──────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Sidebar Filters

### Section 1: Geography

| Control | Type | Behavior |
|---|---|---|
| **Geo Level** | Radio or selectbox | Options: State, Region, Division, County, CBSA (in that order). Default: State. |
| **State Filter** | Multiselect | Appears only when Geo Level = County or CBSA. Lists all 48 contiguous states. Filters both map and table to the selected states. When empty, shows all. |

**48-state rule:** Alaska, Hawaii, and territories (FIPS ≥ 57 except DC, plus AK=02 and HI=15) are excluded from all queries and the map. DC (FIPS=11) is included.

Region and Division geometries are derived at query time by dissolving `geo.states` polygons grouped via `silver.xwalk_state_region`. No separate geometry table needed.

### Section 2: KPIs

| Control | Type | Behavior |
|---|---|---|
| **Subject Area** | Selectbox | Population / Housing / Income. Drives the available KPIs in the pickers below. |
| **Map KPI** | Selectbox | Single KPI, grouped by subject area. This is the field that colors the choropleth. |
| **Table KPIs** | Multiselect | Multiple KPIs from the same subject area. These become columns in the data table. Defaults to all KPIs in the subject area. |

KPI groupings:

**Population** (source: `gold.population_demographics`)
- Total Population, Pop Growth 1yr, Pop Growth 3yr, Pop Growth 5yr, Median Age, Share Under 18, Share Age 65+, Dependents Per Worker, Hispanic Share, Diversity Index, Share With Bachelor's Degree Or Higher

**Housing** (source: `gold.housing_core_wide`)
- Total Housing Units, Vacancy Rate, Owner Occupancy Rate, Renter Occupancy Rate, Median Gross Rent, Annualized Median Rent, Median Home Value, Share Rent Burdened 30%+, Rent To Income Ratio, Home Value To Income Ratio, Permits Per 1,000 Housing Units

**Income** (source: `gold.economics_income_wide`)
- Median Household Income, ACS Per Capita Income, Poverty Rate, Gini Index, Total Personal Income, BEA Per Capita Personal Income, Per Capita Income Growth 1yr, Per Capita Income Growth 5yr, Per Capita Income CAGR 5yr, Wage Share Of Personal Income

### Section 3: Filters

| Control | Type | Behavior |
|---|---|---|
| **Year** | Selectbox | Available years from the selected Gold table. Default: 2024. |
| **KPI Range Slider** | Double-ended slider (min/max) | Dynamically set from the p1–p99 range of the **Map KPI** for the current geo level and year. Filters which rows appear in the table. Map always shows all geographies (unfiltered by range — range filter is table-only). |

---

## Choropleth Map

**Library:** Plotly Express (`px.choropleth_mapbox` or `px.choropleth` with custom GeoJSON).

**Geometry source:**

| Geo Level | Geometry Table | Join Key |
|---|---|---|
| State | `geo.states` | `state_fips = geo_id` |
| County | `geo.counties` | `county_geoid = geo_id` |
| CBSA | `geo.cbsas` | `cbsa_code = geo_id` |
| Region | Dissolved from `geo.states` GROUP BY `census_region` | `census_region = geo_id` |
| Division | Dissolved from `geo.states` GROUP BY `census_division` | `census_division = geo_id` |

Geometry is stored as `geom` (DuckDB GEOMETRY type). Extract as GeoJSON using `ST_AsGeoJSON(geom)` via DuckDB spatial extension. Assemble into a FeatureCollection in Python before passing to Plotly.

**Map behavior:**
- Color scale: Viridis (sequential) for most KPIs; RdBu diverging for growth/ratio metrics
- Hover tooltip: geo_name, KPI display name, formatted value, remaining KPIs in the KPI family
- Null geographies: rendered in light gray with "N/A" in tooltip
- The range slider does NOT filter the map — all geographies render, but out-of-range ones are visually distinct (slightly muted opacity is acceptable but not required in v1)

---

## Data Table

**Content:**
- Always-present columns: `geo_name`, `geo_level`, `geo_id`, `year`
- User-selected KPI columns (formatted per `unit_format`)
- Growth columns appended after KPI columns:
  - For population metrics: `pop_growth_1yr`, `pop_growth_3yr`, `pop_growth_5yr`
  - For housing metrics: shown only for growth-eligible metrics (`hu_total`, `median_gross_rent`, `annualized_median_rent`, `median_home_value`)
  - For income metrics: `income_pc_growth_1yr`, `income_pc_growth_5yr`, `income_pc_cagr_5yr`

**Filtering:** The KPI range slider filters to rows where the **Map KPI** value falls within [min, max]. Nulls in the map KPI are excluded when the slider is active.

**Sorting:** Default sort is descending by the Map KPI. User can click column headers to re-sort.

**Download:** A "Download CSV" button exports the current filtered, sorted table.

**Row count cap:** Show a row count at the top of the table. No hard cap — rely on the state filter and KPI range to reduce County/CBSA result sets.

---

## Value Formatting

| `unit_format` | Display Format |
|---|---|
| `integer` | `1,234,567` |
| `percent` | `12.3%` |
| `currency` | `$54,321` |
| `number_1dp` | `34.2` |
| `ratio` | `0.42` |
| `index` | `0.61` |
| `rate_per_1000` | `8.3 per 1,000` |

Null values display as `—` in the table.

---

## Data Query Pattern

All queries go through DuckDB. Use `@st.cache_data(ttl=3600)` on functions that return DataFrames or GeoJSON to avoid re-querying on each widget interaction.

Typical query shape for a Gold table:
```sql
SELECT geo_id, geo_name, year, <metric_columns>
FROM gold.<table>
WHERE geo_level = '<geo_level>'
  AND year = <year>
  AND geo_id IN (<48-state-filtered geo_ids>)
ORDER BY <map_kpi> DESC NULLS LAST
```

For Region/Division, join through `silver.xwalk_state_region` to get the geo_name label, since the Gold tables use `census_region`/`census_division` codes, not display names.

---

## Performance Notes

- GeoJSON for states (~56 features) and divisions (9) / regions (4) is small — fine to load on every page change.
- County GeoJSON (~3,200 features) is large. Cache it aggressively. When a state filter is active, extract only the matching counties from the FeatureCollection before passing to Plotly.
- CBSA GeoJSON (~935 features) is medium. Cache the full set; filter in Python by state membership using `silver.xwalk_cbsa_state` or `silver.xwalk_cbsa_county`.

---

## File Structure

```
reference_dashboard/
├── data_explorer.py          ← main Streamlit app
└── explorer_utils.py         ← DuckDB query helpers, GeoJSON builder, formatters
```

Fully isolated from `frontend/`. No changes to `streamlit_app.py`, `qa_review.py`, or any other existing frontend files.

---

## Out of Scope (v1)

- Time series charts or trend views (single-year snapshot only)
- Chatbot output ingestion or side-by-side diff panel
- ZCTA and Census Tract geo levels
- Cross-subject-area KPI comparison in the same table
- Map click-to-filter behavior
