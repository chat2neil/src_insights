


# cluster_df = self._cluster_procedures_by_table_and_operation()

# # Step 3: Output the groups of records that are considered to be similar to each other
# for label in cluster_df['cluster_label'].unique():
#     print(f"Cluster {label}:")
#     selected_procs = cluster_df[cluster_df['cluster_label'] == label]
#     print(selected_procs[['procedure_name', 'operation_type', 'table_name', 'cluster_label']].sort_values(by=['procedure_name', 'operation_type', 'table_name']))
