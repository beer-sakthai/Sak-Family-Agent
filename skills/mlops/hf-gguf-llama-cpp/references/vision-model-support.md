# Vision Model Support with llama.cpp

The pre-built llama.cpp binary includes `llama-llava-cli` and `llama-qwen2vl-cli` for running multimodal vision-language models.

## Supported Models

| Model | Binary | Size | 
|-------|--------|:----:|
| LLaVA-v1.5-7B | `llama-llava-cli` | 3.9 GB (Q4_K_M) |
| Qwen2-VL | `llama-qwen2vl-cli` | Various |

## Finding Vision GGUFs

Search HF Hub for pre-quantized vision GGUFs:

```bash
curl -s "https://huggingface.co/api/models?search=llava+gguf+q4&sort=downloads&limit=5"
```

Community users like `Marwan02`, `bartowski`, and `mradermacher` often host vision GGUFs.

## Uploading to Your HF Account

```python
from huggingface_hub import HfApi, create_repo
api = HfApi()
create_repo('your-org/sakthai-vision-7b', repo_type='model', exist_ok=True)
api.upload_file(
    path_or_fileobj='/path/to/model.gguf',
    path_in_repo='gguf/sakthai-vision-q4_k_m.gguf',
    repo_id='your-org/sakthai-vision-7b',
    repo_type='model'
)
```
