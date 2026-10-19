# Data dictionary

CSV files use UTF-8, a header row, commas, decimal points, and empty fields for missing values. Types below describe the intended schema; raw exports may violate it.

## samples.csv

| Column | Intended type | Meaning |
|---|---|---|
| sample_id | text | Unique treatment-well ID, `S` followed by four digits |
| batch_id | text | Acquisition/experimental batch, B01–B06 |
| culture_id | text | Independent culture preparation; paired across four treatment wells |
| treatment | text | `vehicle` or `Compound_A` |
| dose_uM | numeric | Concentration in micromolar: 0, 0.1, 1, or 10; vehicle is 0 |
| exposure_h | integer | Treatment duration, hours |
| plate_id | text | Plate identifier; one plate per batch in this exercise |
| well | text | Well location on a 96-well plate, A01–H12; unique within plate |

## image_measurements.csv

| Column | Intended type | Meaning |
|---|---|---|
| image_id | text | Unique acquisition field ID |
| sample_id | text | Foreign key to samples.sample_id |
| field_index | integer | Field 1–4 within a sample; sample_id + field_index should be unique |
| cell_count | integer | Total segmented cells in the field |
| live_cell_count | integer | Cells classified as live, a subset of cell_count |
| mean_fluorescence_au | numeric | Mean marker fluorescence per segmented cell, arbitrary units; not total field fluorescence |
| focus_score | numeric | Instrument focus score, 0–1; larger is better |
| acquisition_date | date | ISO 8601 acquisition date, YYYY-MM-DD |

Field viability can be calculated as live_cell_count / cell_count when the denominator is positive. When pooling fields, distinguish the ratio of summed counts from the unweighted average of field ratios. Neither should treat duplicate export rows as new observations.

## batch_controls.csv

Controls are separate from the experimental wells and do not have sample IDs. There are three control types with three replicate measurements each per batch.

| Column | Intended type | Meaning |
|---|---|---|
| control_id | text | Unique control measurement ID |
| batch_id | text | Batch associated with the control |
| control_type | text | `blank`, `fluorescence_reference`, or `live_cell_reference` |
| replicate | integer | Control replicate 1–3, unique within batch and control type |
| mean_fluorescence_au | numeric | Mean control fluorescence, arbitrary units |
| reference_cell_count | integer | Total counted reference cells; zero for non-cell controls |
| live_cell_count | integer | Live reference cells; zero for non-cell controls |
| acquisition_date | date | ISO 8601 date |

Do not calculate a viability percentage for blank or fluorescence-reference controls: both counts are zero by design. Fluorescence reference beads contain no cells.
