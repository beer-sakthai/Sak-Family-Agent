# HF Learnings: Spaces Configuration Reference (Topic #274)

## Summary
Complete reference for Hugging Face Spaces YAML configuration system covering all 30+ configuration parameters, 18 hardware flavors (2 CPU + 16 GPU), built-in environment variables, OAuth setup, model preloading, custom headers, SDK-specific behavior, networking, lifecycle management, and programmatic API configuration.

## Key Parameters
- **sdk**: `gradio`, `docker`, `static`, `streamlit` — determines Space framework
- **python_version**: defaults to 3.10, any 3.x or 3.x.x valid
- **sdk_version**: pins Gradio version (all versions supported)
- **app_file**: path to main application file (defaults to `app.py`)
- **suggested_hardware**: 18 flavors from `cpu-basic` (free) to `a100x8` ($20/hr)
- **preload_from_hub**: preload HF models at build time to reduce cold-start
- **custom_headers**: cross-origin isolation headers (COEP, COOP, CORP)
- **hf_oauth**: OAuth app association with configurable scopes and expiry

## Hardware Specs
- CPU Basic: 2 vCPU, 16 GB RAM, 50 GB disk — Free (requires paid plan to create)
- CPU Upgrade: 8 vCPU, 32 GB RAM — $0.03/hr
- GPU range: T4 ($0.40/hr) through A100x8 ($20.00/hr)
- ZeroGPU free tier available for Gradio Spaces (covered elsewhere)

## Built-in Env Vars
9 standard vars (ACCELERATOR, CPU_CORES, MEMORY, SPACE_AUTHOR_NAME, etc.) plus 4 OAuth-related vars (OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET, OAUTH_SCOPES, OPENID_PROVIDER_URL)

## Key Insights
1. **Static Spaces are free** for all users — no paid plan needed
2. **Sleep behavior**: Free Spaces sleep after 48h; paid Spaces run indefinitely unless custom timeout set
3. **Preloading** saves models in `~/.cache/huggingface/hub` at build time, eliminating download latency
4. **Docker Spaces** use `app_port` (default 7860) and support any framework via custom Dockerfile
5. **OAuth tokens** max at 43200 minutes (30 days), default 480 min (8 hours)
6. **Custom headers** only allow COEP, COOP, CORP — all values must be lowercase
7. **No programmatic Space creation** with config YAML — YAML must be in README.md directly
