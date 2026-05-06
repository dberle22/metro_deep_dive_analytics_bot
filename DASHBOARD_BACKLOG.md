# Data Explorer Dashboard — Backlog

Reference spec: [DASHBOARD_SPEC.md](DASHBOARD_SPEC.md)

---

## Sprint 1 — Data Layer & Geometry Foundation

**Goal:** All data queries work correctly and return the right shapes. GeoJSON builds cleanly for all 5 geo levels. No UI yet — only Python functions with manual test calls.

**Files:** `reference_dashboard/explorer_utils.py`

---

### [x] Task 1.1 — DuckDB connection helper

Create `get_connection()` in `explorer_utils.py` that reads `DB_CONNECTION` from `.env` and returns a read-only DuckDB connection. Mirror the pattern already used in `app/query/executor.py`.

**Done when:** `get_connection().execute("SELECT 1").fetchone()` returns `(1,)`.

---

### [x] Task 1.2 — 48-state FIPS allowlist

Build a utility that returns the set of valid state FIPS codes (contiguous US + DC, excluding AK=02, HI=15, territories ≥ 57 except DC=11).

Used as a filter in every downstream query.

**Done when:** The set contains exactly 49 FIPS codes (48 contiguous + DC).

---

### [x] Task 1.3 — GeoJSON builder for states

Write `build_geojson(geo_level: str, state_filter: list[str] | None) -> dict` for `geo_level = "state"`.

Steps:
1. Query `geo.states`: `SELECT state_fips AS geo_id, state_name AS geo_name, ST_AsGeoJSON(geom) AS geojson_str FROM geo.states WHERE state_fips IN (<48-state allowlist>)`
2. Optionally filter by `state_filter` (list of FIPS codes).
3. Assemble a GeoJSON FeatureCollection where each Feature has `properties.geo_id` and `properties.geo_name`.

**Done when:** Result is valid GeoJSON with 49 features (or fewer when state_filter is active). Confirm `len(features) == 49` with no filter.

---

### [x] Task 1.4 — GeoJSON builder for counties

Extend `build_geojson` for `geo_level = "county"`.

Query `geo.counties`: `SELECT county_geoid AS geo_id, county_name AS geo_name, STUSPS AS state_abbr, state_fips, ST_AsGeoJSON(geom) AS geojson_str`.

Apply `state_fips IN (<48-state allowlist>)` always. Apply additional `state_fips IN (<state_filter>)` when provided.

**Done when:** All-states result has ~3,100 features. Single-state result (e.g. TX) has the correct county count.

---

### [x] Task 1.5 — GeoJSON builder for CBSAs

Extend `build_geojson` for `geo_level = "cbsa"`.

Query `geo.cbsas` joined to `silver.xwalk_cbsa_state` to support the state filter: only include CBSAs that have at least one county in the selected states.

`cbsa_code` is the geo_id. Use `cbsa_name` as geo_name.

Apply the 48-state rule by excluding CBSAs whose member counties are exclusively in AK, HI, or territories.

**Done when:** All-states result has ~930 features. State-filtered result returns only CBSAs with membership in selected states.

---

### [x] Task 1.6 — GeoJSON builder for regions and divisions

Extend `build_geojson` for `geo_level = "region"` and `"division"`.

These have no geometry table. Build by:
1. Query `silver.xwalk_state_region` to get `(state_fips, census_region, census_division)`.
2. Join to `geo.states` on `state_fips`.
3. Group by `census_region` (or `census_division`), dissolve geometry using `ST_Union_Agg(geom)`.
4. Use `census_region`/`census_division` code as `geo_id`. Derive `geo_name` from the code (hardcode a small lookup dict: `{"1": "Northeast", "2": "Midwest", "3": "South", "4": "West"}`).

DuckDB spatial extension supports `ST_Union_Agg`. Confirm it's loaded with `LOAD spatial`.

**Done when:** Region result has 4 features covering the contiguous US. Division result has 9 features.

---

### [x] Task 1.7 — Gold table query function

Write `query_gold(geo_level: str, subject_area: str, year: int, state_filter: list[str] | None) -> pd.DataFrame`.

- `subject_area` maps to a Gold table: `population → gold.population_demographics`, `housing → gold.housing_core_wide`, `income → gold.economics_income_wide`.
- Returns all metric columns for the table, filtered to the given `geo_level`, `year`, and (if applicable) state filter.
- For Region and Division geo levels, join to `silver.xwalk_state_region` to translate codes to display names.
- Apply 48-state filter always.

**Done when:** `query_gold("state", "population", 2024, None)` returns a DataFrame with 49 rows and all population metric columns.

---

### [x] Task 1.8 — Growth metrics columns

The Gold tables already contain pre-computed growth columns. Verify which are present and add a `GROWTH_COLUMNS` dict in `explorer_utils.py` mapping subject area to the list of growth column names to always include in the table output:

```python
GROWTH_COLUMNS = {
    "population": ["pop_growth_1yr", "pop_growth_3yr", "pop_growth_5yr"],
    "housing": ["hu_growth_1yr", "hu_growth_3yr", "hu_growth_5yr"],  # verify column names
    "income": ["income_pc_growth_1yr", "income_pc_growth_5yr", "income_pc_cagr_5yr"],
}
```

If housing growth columns are not pre-computed in the Gold table, compute them in the query using LAG or self-join (verify against `gold_housing_core.sql`).

**Done when:** Growth columns appear in the DataFrame returned by `query_gold` for all three subject areas.

---

## Sprint 2 — Sidebar & Filter Wiring

**Goal:** All sidebar controls exist, are wired to session state, and drive the correct query calls. No map yet — display raw DataFrame output below the sidebar to confirm wiring.

**Files:** `reference_dashboard/data_explorer.py`

---

### [x] Task 2.1 — App scaffold and page config

Create `reference_dashboard/data_explorer.py` with:
- `st.set_page_config(layout="wide", page_title="Data Explorer")`
- A page title and short description
- Sidebar section headers: "Geography", "KPIs", "Filters"
- Import `explorer_utils`

---

### [x] Task 2.2 — Geo Level and State Filter controls

In the Geography section:
- `geo_level`: `st.radio` with options `["State", "Region", "Division", "County", "CBSA"]`
- `state_filter`: `st.multiselect` listing all 48 contiguous state names (+ DC). Only rendered when `geo_level` is County or CBSA. When empty, treat as "all states".

Store selections in `st.session_state`.

---

### [x] Task 2.3 — Subject Area and KPI controls

In the KPIs section:
- `subject_area`: `st.selectbox` with `["Population", "Housing", "Income"]`
- `map_kpi`: `st.selectbox` showing the display names of all metrics for the selected subject area, grouped logically (use `optgroup`-style headers if Streamlit supports it, otherwise a flat sorted list is fine)
- `table_kpis`: `st.multiselect` with the same KPI list, defaulting to all KPIs selected

When `subject_area` changes, reset `map_kpi` and `table_kpis` to defaults.

---

### [x] Task 2.4 — Year selector

In the Filters section:
- Query the available years for the selected Gold table and geo level: `SELECT DISTINCT year FROM gold.<table> WHERE geo_level = '<geo_level>' ORDER BY year DESC`
- `year`: `st.selectbox` from that list, default to 2024 if present.

---

### [x] Task 2.5 — KPI Range Slider

In the Filters section, below the year selector:
- After the main data query runs, compute the p1 and p99 of the Map KPI column (ignoring nulls).
- Render `st.slider` with those as the min/max bounds and the full range as default values.
- Label it with the Map KPI display name.
- This filter applies to the table only (not the map).

---

### [x] Task 2.6 — Debug data output

Below the sidebar controls, render `st.dataframe(df)` where `df` is the result of `query_gold(...)` with the current filter state. This is a development scaffolding step — remove it in Sprint 4 once the real table is built.

**Done when:** Changing any sidebar control updates the displayed DataFrame correctly.

---

## Sprint 3 — Choropleth Map

**Goal:** A working choropleth that renders for all 5 geo levels, colored by the selected Map KPI, with correct tooltips.

**Files:** `reference_dashboard/data_explorer.py`, `reference_dashboard/explorer_utils.py`

---

### [x] Task 3.1 — GeoJSON caching

Wrap all `build_geojson` calls with `@st.cache_data(ttl=3600)`. The GeoJSON for states, regions, and divisions should be loaded once per session. For counties and CBSAs, cache by `(geo_level, tuple(sorted(state_filter)))`.

---

### [x] Task 3.2 — Merge GeoJSON with KPI data

Write `merge_for_map(geojson: dict, df: pd.DataFrame, kpi_col: str) -> dict` in `explorer_utils.py`.

For each feature in the FeatureCollection, look up the matching row in `df` by `geo_id` and add the KPI value and `geo_name` as feature properties. Features with no match get `kpi_value = None`.

---

### [x] Task 3.3 — Plotly choropleth component

Render the map using `px.choropleth_mapbox`:
- `geojson`: merged FeatureCollection from Task 3.2
- `locations`: `geo_id` from the DataFrame
- `color`: the Map KPI column
- `featureidkey`: `"properties.geo_id"`
- `mapbox_style`: `"carto-positron"` (no API key required)
- `center`: `{"lat": 38.5, "lon": -96}` (centers the contiguous US)
- `zoom`: 3
- `color_continuous_scale`: Viridis for absolute metrics; RdBu for growth/ratio metrics (determine by checking if the metric's `unit_format` is `percent` or `ratio` with a natural zero)
- `hover_data`: `geo_name` and the formatted KPI value
- Height: 450px

Apply `fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})` for a clean edge-to-edge look.

---

### [x] Task 3.4 — Null and missing geography handling

Geographies with a null KPI value should render in light gray. Plotly handles nulls as transparent by default — override with a custom colorscale that maps `None` to `#d0d0d0`.

Add a note in the map caption: `"Gray areas indicate missing data for the selected KPI and year."`

---

### [x] Task 3.5 — Map caption and metadata

Below the map, render a single line:
`"Showing {kpi_display_name} at the {geo_level} level • Year: {year} • {n} geographies"`

---

## Sprint 4 — Data Table

**Goal:** A clean, formatted, sortable, downloadable data table driven by the sidebar filters. Growth columns always present.

**Files:** `reference_dashboard/data_explorer.py`, `reference_dashboard/explorer_utils.py`

---

### [x] Task 4.1 — Value formatter

Write `format_value(value, unit_format: str) -> str` in `explorer_utils.py` per the formatting spec:

| `unit_format` | Format |
|---|---|
| `integer` | `f"{value:,.0f}"` |
| `percent` | `f"{value*100:.1f}%"` (values stored as 0–1 decimals) |
| `currency` | `f"${value:,.0f}"` |
| `number_1dp` | `f"{value:.1f}"` |
| `ratio` | `f"{value:.2f}"` |
| `index` | `f"{value:.2f}"` |
| `rate_per_1000` | `f"{value:.1f} per 1,000"` |
| null | `"—"` |

Also write `format_dataframe(df: pd.DataFrame, metric_meta: list[dict]) -> pd.DataFrame` that applies `format_value` to each metric column based on its `unit_format` from the metric catalog.

---

### [x] Task 4.2 — Apply KPI range filter

Before rendering the table, filter `df` to rows where `df[map_kpi_col]` is between `slider_min` and `slider_max` (inclusive). Exclude nulls in the map KPI when the slider is non-default.

---

### [x] Task 4.3 — Column selection and ordering

Build the display DataFrame with columns in this order:
1. `geo_name` (always)
2. `geo_id` (always, as a reference)
3. User-selected Table KPIs (in the order they appear in the multiselect)
4. Growth columns for the subject area (appended at the end, labeled clearly)

Drop `geo_level` and `year` from the display (they're constant for the current view).

---

### [x] Task 4.4 — Render table and download button

Replace the Sprint 2.6 debug output with:
- Row count: `st.caption(f"{len(df_filtered):,} geographies")`
- `st.dataframe(df_display, use_container_width=True)` with `height=400`
- A `st.download_button` that streams the unformatted `df_filtered` as CSV (preserve numeric values for download, not the formatted strings)

---

### [x] Task 4.5 — Remove Sprint 2.6 debug output

Delete the raw `st.dataframe(df)` scaffolding added in Sprint 2.6.

---

## Sprint 5 — Polish, Performance & QA

**Goal:** The app is performant, handles edge cases gracefully, and is ready for use as a QA reference tool.

---

### [x] Task 5.1 — Cache audit

Confirm `@st.cache_data` is applied to:
- `build_geojson` (all variants)
- `query_gold`
- `get_available_years`

Confirm nothing that mutates state is cached (sliders, session state writes).

---

### [x] Task 5.2 — Empty-state handling

Handle these edge cases cleanly:
- No data returned for selected geo_level + year (show `st.warning`)
- All values null for the Map KPI (show `st.warning` on the map, disable the slider)
- State filter active with no matching CBSAs or counties (show `st.info`)

---

### [x] Task 5.3 — Loading spinners

Wrap the map render and table render sections in `with st.spinner("Loading...")`. Long queries (county GeoJSON, full county data pull) should feel responsive rather than frozen.

---

### [x] Task 5.4 — Income metric geo level guard

Some income metrics (`median_hh_income`, `acs_income_pc`, etc.) are only valid at `state`, `cbsa`, `county` — not at `region` or `division`. When the user selects Region or Division with an income metric, show a `st.warning` explaining the limitation. Either hide income metrics in the KPI picker or grey them out when the geo level doesn't support them.

Cross-reference `valid_geo_levels` in `metric_catalog.yml`.

---

### [x] Task 5.5 — Manual QA pass

Run through this checklist before marking the dashboard complete:

- [x] State level, all 3 subject areas, 2024
- [x] County level with a state filter (TX), Population KPI, range slider active
- [x] CBSA level with a state filter (FL), Housing KPI
- [x] Region and Division levels, Income KPI (expect warning or graceful null handling)
- [x] Download CSV works and contains numeric (not formatted string) values
- [x] Switching subject area resets KPI pickers without error
- [x] Switching geo level resets state filter visibility correctly

---

## Dependency Notes

- DuckDB spatial extension must be loaded: `con.execute("LOAD spatial")` before any `ST_AsGeoJSON` call.
- `plotly` must be in `requirements.txt` (may already be present).
- No new Python packages needed beyond what's already in the repo venv.

---

## Launch Command

```bash
.venv/bin/python -m streamlit run reference_dashboard/data_explorer.py
```
