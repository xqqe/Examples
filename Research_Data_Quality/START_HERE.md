# Research Data Quality and Experiment Analysis

**All records are synthetic.** This is an educational dataset, not a real biological study. The CSVs contain measurements and metadata, not microscopy image files.

## The experiment

A fictional cell culture study asks whether Compound A changes cell abundance, viability, and mean cellular fluorescence after 24 hours. Six batches were acquired on separate days. Each batch contains eight independently established culture preparations. Each culture preparation was split into four wells: vehicle (0 µM) and Compound A at 0.1, 1, and 10 µM. Four non-overlapping fields were acquired per well using the same nominal field area and exposure settings.

There are **48 independent culture preparations, 192 treatment wells, and 768 planned image fields**. The export may contain more or fewer records than the design expects. There are also 54 separate control measurements.

A well is the treatment unit. Wells from the same culture are paired; they are not independent biological preparations. The four image fields from a well are technical subsamples, not four biological replicates. Culture preparations are unique to a batch; do not assume the same culture was measured repeatedly across days.

Cell counts are endpoint abundance measurements. Without baseline counts, they cannot directly establish growth rates or distinguish reduced proliferation from other causes of lower abundance.

## Files and relationships

| File | Intended row | Intended identifier / relationship |
|---|---|---|
| `data/raw/samples.csv` | One treatment well | `sample_id`; includes culture and batch metadata |
| `data/raw/image_measurements.csv` | One image field | `image_id`; `sample_id` joins to samples |
| `data/raw/batch_controls.csv` | One control replicate | `control_id`; `batch_id` joins to batches represented in samples |

Raw exports may contain data quality problems. Preserve these files unchanged. Record decisions in your own analysis rather than manually fixing the originals. Do not force raw data into a schema that discards problematic rows before you can audit them.

## Predeclared QC criteria

These rules are supplied as study specifications, not inferred from the observed treatment results.

- Sample/image/control identifiers must be present; identifiers should be consistent across tables.
- Counts must be non-negative integers; live-cell count must not exceed total cell count.
- Fluorescence measurements must be non-negative. Missing endpoints must be recorded explicitly, not silently interpreted as zero.
- Images with focus score below **0.70** fail image focus QC.
- The fluorescence reference target is **1,000 AU**. Its batch median must be within **850–1,150 AU**.
- The blank batch median must be below **60 AU**.
- The live-cell reference batch median viability must be at least **90%**. Calculate each control's viability as `live_cell_count / reference_cell_count`; this ratio applies only to live-cell references.
- Failing one control does not automatically invalidate every endpoint. Document what a failure implies and compare defensible analysis choices. A reference-based correction requires an explicit assumption about instrument response.
- Unusually large but physically possible measurements should be flagged and investigated, not automatically deleted.

The design specifies four fields per well. Report usable field counts after QC. If some fields or endpoints are missing, choose and justify how to summarize them; do not invent replacement measurements.

## Your first task

Load each CSV in Python. Print its shape, first five rows, column types, and missing-value counts. Then compare the number of rows with the number of unique intended identifiers. Do not clean anything yet.

Later tasks: audit relationships, design SQL tables, write QC queries, summarize wells, visualize dose responses, and analyze the paired/batched design. Keep a decision log and show how conclusions change under important QC choices.

## Reproducibility and attribution

Dataset version 1.0; generated with Python standard-library random seed 20261019. Synthetic data and exercise design were generated with ChatGPT for this learning project. No patient, employer, or proprietary data are included. A separate reference archive retains the generator and issue ledger; it is intentionally excluded from this learner package to avoid revealing the exercise answers.
