# Line Chart Testing

## Inputs
- Dataset: `visual_sample_line`
- Prep function: `prep_line`
- Render function: `render_line`

## Business Questions to Test
1. Single-series: How has Wilmington population changed from 2013 to 2023?
2. Multi-series: How does Wilmington compare with selected peers over time?
3. Indexed comparison: Are housing costs rising faster than incomes over time (base year = 2013)?

## Test Procedure
1. Build sample data with `sample_sql/build_line_sample.sql`.
2. Run `test_line_render.R`, which queries DuckDB directly for each question.
3. Use `prep_line` in variant mode (`single`, `multi`, `indexed`).
4. Render charts with `render_line` and include question text in subtitle.
4. Save PNG outputs in this folder.
5. Verify period range, transform label, legend readability, and source/vintage caption.

## Expected Outputs
- `line_test_single.png`
- `line_test_multi.png`
- `line_test_indexed.png`
