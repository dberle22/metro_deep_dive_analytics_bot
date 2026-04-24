# Frontend
## US Demographic and Economic Analytics Chatbot

## 1. Purpose

The frontend provides a simple, analytical interface for asking questions about US demographic and economic data and reviewing trusted results.

The MVP frontend should feel more like an analytical application than a general chatbot, while still allowing natural language interaction and lightweight follow up questions.

## 2. User Experience Goals

The frontend should be:

- clean
- minimal
- analytical
- low decoration
- chart forward
- easy to inspect

The interface should help users move quickly from question to result, while making the answer, chart, table, SQL, and assumptions easy to review.

## 3. Main Screen Layout

### Layout Pattern
The MVP should use a single page layout with:

- question input at the top
- results below
- lightweight recent history support

This keeps the experience simple and focused while avoiding a full chat heavy interface.

### Landing State
The landing state should include:

- a prominent question input
- a small mixed set of example prompts
- a brief description of what the app supports

Example prompts should represent a mix of:
- rankings
- trends
- comparisons
- benchmarks
- distributions

## 4. Core Interactions

### Primary Interaction
The main interaction is natural language question entry.

Users ask a question and receive:
- a written answer
- a chart
- a result table
- assumptions and definitions
- SQL
- technical details

### Follow Up Interaction
Follow up questions should use the same input as the first question.

The UI should also support:
- suggested follow up chips
- lightweight quick action buttons where useful

Examples:
- show counties instead
- compare against the US
- use 3 year growth
- sort descending

### Clarification Interaction
When the system needs more detail, clarification should appear as:

- an inline assistant style message
- structured prompt options where possible

This is especially important for:
- unclear geography grain
- unclear benchmark choice
- unsupported time logic
- incomplete peer group references

## 5. Result and Detail Panels

### Result Priority
The main result area should prioritize content in this order:

1. chart
2. written answer
3. result table
4. assumptions and definitions
5. SQL
6. technical details

### Main Result Components
Each result should include:

- chart as the primary focal point
- concise written summary
- sortable result table
- assumptions and metric definitions
- SQL used
- expandable technical details

### Detail Display Pattern
SQL and technical details should appear in collapsed accordions below the main result.

This keeps the interface clean by default while still supporting transparency and inspection.

## 6. Result Table Behavior

The result table should support:

- column sorting
- CSV download
- row selection
- full screen expansion

### Peer Group Interaction
For MVP, peer groups should be limited to predefined groups.

The frontend should not include a visible custom peer group builder yet.

Custom peer group creation is a post MVP enhancement.

## 7. History and Follow Up Behavior

### Session History
The MVP should include lightweight recent history support.

This should help users understand recent analyses without turning the interface into a full chat application.

A future version can expand this into:
- scrollable conversation history
- left side chat navigation
- multiple saved analysis threads

### Follow Up State
Follow up questions should inherit relevant context from the prior result.

Expected retained state:
- metric or measure
- geography grain
- geography filters
- benchmark type
- time window
- growth window
- chart intent where applicable

### Quick Actions
The interface should support lightweight quick actions to reduce retyping.

Examples:
- switch geography level
- switch benchmark
- switch growth window
- change sort direction

## 8. States and Edge Cases

### Supported Answer State
Show:
- chart
- answer
- table
- accordions for SQL and technical details

### Clarification State
If the request is recoverable but unclear:
- ask a clarification question
- provide structured options where possible

### Unsupported State
If the request is not supported:
- provide a clear message
- suggest rewritten questions that fit the app’s scope

### Empty or Loading State
The app should handle loading and empty result states cleanly and minimally.

### Error State
If the system fails during planning, query execution, or rendering:
- show a simple error message
- avoid exposing raw stack traces in the main UI
- retain enough information in logs for debugging

## 9. Export and Action Support

### MVP Actions
Include:
- copy SQL
- download result table as CSV

### Post MVP Actions
Later additions can include:
- chart export
- save analysis state
- saved question library
- reusable peer group workflows

## 10. Device Scope

The MVP should be desktop first.

Responsive behavior can improve later, but mobile optimization is not required for the first version.

## 11. Open UI Decisions

The following decisions can be finalized during implementation:

- exact layout of the recent history module
- where suggested follow up chips should appear
- which quick actions are shown by default
- how much explanatory text the landing state should include
- whether the full screen table view is inline or modal
- when chart export is introduced after MVP