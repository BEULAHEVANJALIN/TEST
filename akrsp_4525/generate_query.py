import pandas as pd
import numpy as np


csv_file_path = 'output.csv'
df = pd.read_csv(csv_file_path)

values_clause = ",\n        ".join([
    f"('{row['individual_uuid']}', '{row['individual_uuid_to_merge_into']}')"
    for _, row in df.iterrows()
])

uuids_to_be_merged = "', '".join(df['individual_uuid'].unique())
uuids_to_be_merged = f"'{uuids_to_be_merged}'"

verify_query_before_update1 = f"""
-- total number of encounters that need to be moved
SELECT COUNT(*)
    FROM individual i
             JOIN encounter e ON i.id = e.individual_id
    WHERE i.uuid IN ({uuids_to_be_merged})
      AND e.encounter_date_time IS NOT NULL; -- 1275
"""

uuids_to_be_retained = "', '".join(df['individual_uuid_to_merge_into'].unique())
uuids_to_be_retained = f"'{uuids_to_be_retained}'"

verify_query_before_update2 = f"""
-- total number of encounters that need to be retained
SELECT COUNT(*)
    FROM individual i
             JOIN encounter e ON i.id = e.individual_id
    WHERE i.uuid IN ({uuids_to_be_retained})
      AND e.encounter_date_time IS NOT NULL; -- 437
"""

update_query = f"""
-- update query
WITH csv_data(individual_uuid, individual_uuid_to_merge_into) AS (
    VALUES
        {values_clause}
),
mapped_data AS (
    SELECT 
        ind.id AS individual_id,
        key_ind.id AS merge_into_id,
        ind.uuid AS individual_uuid,
        key_ind.uuid AS merge_into_uuid
    FROM csv_data
    LEFT JOIN individual ind ON ind.uuid = csv_data.individual_uuid
    LEFT JOIN individual key_ind ON key_ind.uuid = csv_data.individual_uuid_to_merge_into
)
INSERT INTO encounter (
    observations,
    encounter_date_time,
    encounter_type_id,
    individual_id,
    uuid,
    version,
    organisation_id,
    is_voided,
    audit_id,
    encounter_location,
    earliest_visit_date_time,
    max_visit_date_time,
    cancel_date_time,
    cancel_observations,
    cancel_location,
    name,
    legacy_id,
    created_by_id,
    last_modified_by_id,
    created_date_time,
    last_modified_date_time,
    address_id,
    sync_concept_1_value,
    sync_concept_2_value,
    manual_update_history,
    filled_by_id
)
SELECT 
    e.observations,
    e.encounter_date_time,
    e.encounter_type_id,
    mapped_data.merge_into_id AS individual_id,
    uuid_generate_v4(),
    e.version,
    e.organisation_id,
    e.is_voided,
    e.audit_id,
    e.encounter_location,
    e.earliest_visit_date_time,
    e.max_visit_date_time,
    e.cancel_date_time,
    e.cancel_observations,
    e.cancel_location,
    e.name,
    e.legacy_id,
    e.created_by_id,
    (SELECT id FROM public.users WHERE username = 'beulah@wimc') AS last_modified_by_id,
    e.created_date_time,
    CURRENT_TIMESTAMP + (RANDOM() * 1000 * (INTERVAL '1 millisecond')) AS last_modified_date_time,
    e.address_id,
    e.sync_concept_1_value,
    e.sync_concept_2_value,
    append_manual_update_history(e.manual_update_history, ' | Merge encounters as part of data cleanup | #4525'),
    e.filled_by_id
FROM encounter e
INNER JOIN mapped_data
    ON e.individual_id = mapped_data.individual_id
WHERE e.encounter_date_time IS NOT NULL
  AND e.organisation_id = (SELECT id FROM organisation WHERE name = 'Ward Implementation and Management Committee - AKRSP'); -- 1275 rows affected
"""

all_uuids = np.concatenate((df['individual_uuid'].unique(), df['individual_uuid_to_merge_into'].unique()))

all_uuids = "', '".join(all_uuids)
all_uuids = f"'{all_uuids}'"

verify_query_after_update = f"""
-- total number of encounters after the update
SELECT COUNT(*)
    FROM individual i
             JOIN encounter e ON i.id = e.individual_id
    WHERE i.uuid IN ({all_uuids})
      AND e.encounter_date_time IS NOT NULL; -- 2987
"""

query_path = 'query.sql'

with open(query_path, 'w') as file:
    file.write('SET ROLE wimc;\n\nBEGIN TRANSACTION;')

with open(query_path, 'a') as file:
    file.write('\n\n')
    file.write(verify_query_before_update1)

with open(query_path, 'a') as file:
    file.write('\n\n')
    file.write(verify_query_before_update2)

with open(query_path, 'a') as file:
    file.write('\n\n')
    file.write('-- total updates should be 1275')

with open(query_path, 'a') as file:
    file.write('\n\n')
    file.write(update_query)

with open(query_path, 'a') as file:
    file.write('\n\n')
    file.write('-- Therefore total encounters after update:\nselect (1275*2) + 437; -- = 2987\n')
    file.write(verify_query_after_update)

with open(query_path, 'a') as file:
    file.write('\n\n')
    file.write('-- COMMIT;\n\nROLLBACK;')

print(f"Generated update_query saved to {query_path}")
