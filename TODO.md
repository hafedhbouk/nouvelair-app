# TODO - pytest collection warnings in ai_testing/ai_test_tools.py

- [ ] Rename helper classes in `ai_testing/ai_test_tools.py` to remove `Test*` prefix:
  - TestDataGenerator -> DataGenerator
  - TestAnomalyDetector -> AnomalyDetector
  - TestCoverageAnalyzer -> CoverageAnalyzer
- [ ] Update references in `main()` accordingly.
- [x] Re-run: `pytest ai_testing/ai_test_tools.py` to verify no PytestCollectionWarning and behavior is clean.

- [ ] (Optional) Re-run full `pytest` suite to ensure nothing else depends on the old class names.

