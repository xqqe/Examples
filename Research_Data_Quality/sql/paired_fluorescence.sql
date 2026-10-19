WITH eligible_wells AS (
    SELECT
        sample_id,
        batch_id,
        culture_id,
        treatment,
        dose_uM,
        mean_fluorescence_au
    FROM well_summary
    WHERE condition_resolved = 1
      AND n_fields_fluorescence >= 3
      AND mean_fluorescence_au IS NOT NULL
),

vehicle_wells AS (
    SELECT *
    FROM eligible_wells
    WHERE treatment = 'vehicle'
      AND dose_uM = 0
),

treated_wells AS (
    SELECT *
    FROM eligible_wells
    WHERE treatment = 'Compound_A'
      AND dose_uM > 0
)

SELECT
    t.batch_id,
    t.culture_id,
    t.sample_id AS treated_sample_id,
    v.sample_id AS vehicle_sample_id,
    t.dose_uM,

    t.mean_fluorescence_au AS treated_fluorescence,
    v.mean_fluorescence_au AS vehicle_fluorescence,

    t.mean_fluorescence_au
        - v.mean_fluorescence_au AS fluorescence_difference,

    t.mean_fluorescence_au
        / NULLIF(v.mean_fluorescence_au, 0) AS fluorescence_fold_change

FROM treated_wells AS t
JOIN vehicle_wells AS v
    ON t.culture_id = v.culture_id
   AND t.batch_id = v.batch_id

ORDER BY t.dose_uM, t.batch_id, t.culture_id;