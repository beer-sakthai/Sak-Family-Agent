---
name: SakThai-hf-datasets-video-processing
description: "Covers the datasets.Video feature — loading, decoding, transforming, encoding, and streaming video data through the Hugging Face datasets library."
---

## Description
Covers the `datasets.Video` feature — loading, decoding, transforming, encoding, and streaming video data through the Hugging Face `datasets` library (v5.0.0+). Handles all input types (paths, bytes, dicts, torchcodec VideoDecoder objects), the VideoFolder dataset builder for zero-code dataset creation, WebDataset TAR-based scaling for large video corpora, Lance format for multimodal blob storage, and on-the-fly frame extraction using torchcodec. Focused on patterns that work under zero-cost constraints.

## Key Resources
- [Video feature API reference](https://huggingface.co/docs/datasets/en/package_reference/main_classes#datasets.Video)
- [Video dataset loading guide](https://huggingface.co/docs/datasets/en/video_dataset)
- [Create a video dataset guide](https://huggingface.co/docs/datasets/en/video_dataset#create-a-video-dataset)
- [TorchCodec documentation](https://meta-pytorch.org/torchcodec)
- [VideoFolder builder](https://huggingface.co/docs/datasets/en/video_dataset#videofolder)
- [WebDataset format](https://huggingface.co/docs/datasets/en/video_dataset#webdataset)
- [Lance format](https://huggingface.co/docs/datasets/en/video_dataset#lance)
- [Streaming documentation](https://huggingface.co/docs/datasets/en/stream)

## Topics Covered
- `Video()` feature: decode=True/False, stream_index, dimension_order (NCHW/NHWC), device, seek_mode
- Arrow storage layer: `struct<bytes: binary, path: string>` and cast_storage from string/binary/list types
- torchcodec VideoDecoder as the decoding backend (FFmpeg-based)
- Streaming video datasets with `load_dataset(streaming=True)`
- VideoFolder: directory-structured datasets with automatic label inference
- Metadata CSV/JSONL/Parquet integration for captions, bboxes, multi-video rows
- WebDataset TAR archives for large-scale video (1GB per shard)
- Lance format: native blob storage for video + metadata as a single artifact
- Memory-efficient patterns: deferred decode, embed_storage, in-memory bytes
- Input types: paths, Path objects, bytes/bytearray, numpy arrays, VideoDecoder objects
- Private repo video access via token_per_repo_id and hf_video_reader
- Encoding videos back to bytes (limitations with raw VideoDecoder objects)
- Multi-video rows via file_names/*_file_names fields in metadata
- Video + audio captioning datasets with text fields
