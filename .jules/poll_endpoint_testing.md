# Learned: Testing Top-Level Scripts

- To test top-level scripts, move their main logic into testable functions (`main()` and feature-specific functions).
- `unittest.mock.patch` and `MagicMock` are highly effective for mocking external API client behavior (such as `huggingface_hub.HfApi`) without needing a live network connection.
- A dummy class (like `DummyEndpoint`) is useful for mocking response objects that have specific attributes expected by the code.
- Always ensure side effects (like `time.sleep`) are mocked in tests to prevent tests from running slowly or timing out.
