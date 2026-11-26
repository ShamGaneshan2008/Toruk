| Original failed test | Classification | Repair / execution contract |
| --- | --- | --- |
| `tests/test_first_byte_probe.py::test_exact_saved_inputs_and_260_record_plan` | optional-local-checkpoints | Explicit missing-input skip; portable plan checks and separate exact-hash CLI |
| `tests/test_lifetime_job.py::test_controller_always_records_and_kernel_closes_lifetime[success-0]` | native-Windows-Job | Run unchanged test on Windows; explicit Ubuntu skip |
| `tests/test_lifetime_job.py::test_controller_always_records_and_kernel_closes_lifetime[failure-7]` | native-Windows-Job | Run unchanged test on Windows; explicit Ubuntu skip |
| `tests/test_lifetime_job.py::test_controller_always_records_and_kernel_closes_lifetime[interrupt-130]` | native-Windows-Job | Run unchanged test on Windows; explicit Ubuntu skip |
| `tests/test_lifetime_job.py::test_abrupt_exit_without_self_receipt_is_completely_accounted` | native-Windows-Job | Run unchanged test on Windows; explicit Ubuntu skip |
| `tests/test_lifetime_job.py::test_cap_and_observer_interruption_drain_entire_tree[False]` | native-Windows-Job | Run unchanged test on Windows; explicit Ubuntu skip |
| `tests/test_lifetime_job.py::test_cap_and_observer_interruption_drain_entire_tree[True]` | native-Windows-Job | Run unchanged test on Windows; explicit Ubuntu skip |
| `tests/test_lifetime_job.py::test_descendant_outlives_parent_and_lifetime_cpu_exceeds_coarse_samples` | native-Windows-Job | Run unchanged test on Windows; explicit Ubuntu skip |
| `tests/test_lifetime_job_v2.py::test_normal_exit_closes_receipt_streams_and_seals_stable_bytes` | sealer-fixture-outside-checkout | Confine fresh pytest temporary files to checkout; native creation on Windows |
| `tests/test_lifetime_job_v2.py::test_stopped_workloads_retain_partial_output_and_complete_receipt[timeout]` | sealer-fixture-outside-checkout | Confine fresh pytest temporary files to checkout; native creation on Windows |
| `tests/test_lifetime_job_v2.py::test_stopped_workloads_retain_partial_output_and_complete_receipt[observer-interruption]` | sealer-fixture-outside-checkout | Confine fresh pytest temporary files to checkout; native creation on Windows |
| `tests/test_lifetime_job_v2.py::test_stopped_workloads_retain_partial_output_and_complete_receipt[failure]` | sealer-fixture-outside-checkout | Confine fresh pytest temporary files to checkout; native creation on Windows |
| `tests/test_lifetime_job_v2.py::test_stopped_workloads_retain_partial_output_and_complete_receipt[abrupt]` | sealer-fixture-outside-checkout | Confine fresh pytest temporary files to checkout; native creation on Windows |
| `tests/test_lifetime_job_v2.py::test_late_descendant_log_and_payload_write_precede_final_cost_and_seal` | sealer-fixture-outside-checkout | Confine fresh pytest temporary files to checkout; native creation on Windows |
| `tests/test_lifetime_job_v2.py::test_post_seal_mutations_are_detected[payload]` | sealer-fixture-outside-checkout | Confine fresh pytest temporary files to checkout; native creation on Windows |
| `tests/test_lifetime_job_v2.py::test_post_seal_mutations_are_detected[monitor]` | sealer-fixture-outside-checkout | Confine fresh pytest temporary files to checkout; native creation on Windows |
| `tests/test_lifetime_job_v2.py::test_post_seal_mutations_are_detected[receipt]` | sealer-fixture-outside-checkout | Confine fresh pytest temporary files to checkout; native creation on Windows |
| `tests/test_lifetime_job_v2.py::test_post_seal_mutations_are_detected[added-file]` | sealer-fixture-outside-checkout | Confine fresh pytest temporary files to checkout; native creation on Windows |
| `tests/test_lifetime_job_v2.py::test_post_seal_mutations_are_detected[removed-file]` | sealer-fixture-outside-checkout | Confine fresh pytest temporary files to checkout; native creation on Windows |
| `tests/test_lifetime_job_v2.py::test_overwrite_and_reseal_refusal_preserve_existing_valid_run` | sealer-fixture-outside-checkout | Confine fresh pytest temporary files to checkout; native creation on Windows |
| `tests/test_lifetime_job_v2.py::test_missing_final_receipt_retains_failure_marker_and_partial_output` | sealer-fixture-outside-checkout | Checkout-confined fixture; keep unchanged portable rejection test on both OSes |
| `tests/test_lifetime_job_v2.py::test_interrupted_seal_publication_retains_incomplete_seal_and_failure` | native-Windows-Job | Run unchanged test on Windows; explicit Ubuntu skip |
| `tests/test_lifetime_job_v2.py::test_cli_verification_and_trusted_seal_digest` | sealer-fixture-outside-checkout | Confine fresh pytest temporary files to checkout; native creation on Windows |
| `tests/test_lifetime_job_v2.py::test_unclosed_final_receipt_cannot_be_sealed` | sealer-fixture-outside-checkout | Checkout-confined fixture; keep unchanged portable rejection test on both OSes |
| `tests/test_lifetime_job_v2.py::test_cli_run_uses_observer_owned_sealing` | sealer-fixture-outside-checkout | Confine fresh pytest temporary files to checkout; native creation on Windows |
| `tests/test_paired_batch_dev.py::test_fixed_models_initialize_to_original_hashes_without_updates` | archived-runtime-initialization | Keep recorded expected hashes; qualify archival test by runtime; diagnose both OSes |
| `tests/test_qwen_development_v4.py::test_saved_development_audit_has_no_candidate_or_heldout_input` | historical-versus-current-attributes | Verify original publication blob/hash-bound shallow snapshot; check current attrs separately |
| `tests/test_qwen_long_history_v2.py::test_rehearsal_stops_on_first_failure_and_restores_power` | native-ctypes-windll | Run unchanged test on Windows; explicit Ubuntu skip |
