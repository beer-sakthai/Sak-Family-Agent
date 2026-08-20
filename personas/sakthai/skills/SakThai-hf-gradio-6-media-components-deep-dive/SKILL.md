---
name: SakThai-hf-gradio-6-media-components-deep-dive
description: "Complete reference for Gradio 6 media components \u2014 Audio, Video, Image, File,\
  \ Gallery, and ImageEditor. Covers API surface, streaming, preprocessing, events,\
  \ theming, and advanced usage patterns."
---

# Gradio 6 Media Components — Complete Reference

> **Gradio 6.20.0** (current as of July 2026) introduced significant improvements to all media components: Audio waveform editing, Video subtitle support, ImageEditor brush/eraser tools, Gallery preview events, and File directory uploads.

## Quick Reference Table

| Component | Input | Output | Streaming | Key Events | Data Model |
|-----------|-------|--------|-----------|------------|------------|
| `gr.Audio` | ✓ | ✓ | ✓ (mic→stream, yield→play) | `stream, change, play, pause, stop, start_recording, pause_recording, stop_recording, upload, input, clear` | `FileData` → `(int, np.ndarray)` or `str` |
| `gr.Video` | ✓ | ✓ | ✓ (yield .ts chunks → play) | `change, clear, start_recording, stop_recording, play, pause, stop, end, upload, input` | `FileData` → `str` |
| `gr.Image` | ✓ | ✓ | ✓ (webcam→stream) | `clear, change, stream, select, upload, input` | `ImageData` → `np.ndarray`, `PIL.Image`, or `str` |
| `gr.File` | ✓ | ✓ | ✗ | `change, select, clear, upload, delete, download` | `FileData` / `ListFiles` → `str` / `bytes` |
| `gr.Gallery` | ✓ | ✓ | ✗ | `select, upload, change, delete, preview_close, preview_open` | `GalleryData` (list of images/videos + captions) |
| `gr.ImageEditor` | ✓ | ✓ | ✗ | `change, input, clear, upload, apply` | `EditorData` (background, layers, composite) |

## 1. gr.Audio

### Constructor Parameters

```python
gr.Audio(
    value: str | Path | tuple[int, np.ndarray] | Callable | None = None,
    *,
    sources: list[Literal["upload", "microphone"]] | Literal["upload", "microphone"] | None = None,
    type: Literal["numpy", "filepath"] = "numpy",
    streaming: bool = False,
    format: Literal["wav", "mp3"] | None = None,
    autoplay: bool = False,
    editable: bool = True,
    buttons: list[Literal["download", "share"] | Button] | None = None,
    waveform_options: WaveformOptions | dict | None = None,
    loop: bool = False,
    recording: bool = False,
    subtitles: str | Path | list[dict[str, Any]] | None = None,
    playback_position: float = 0,
    # ... plus standard params (label, every, inputs, show_label, container, scale, min_width, interactive, visible, elem_id, elem_classes, render, key, preserved_by_key)
)
```

### Key Features

| Feature | Description |
|---------|-------------|
| **Waveform display** | `WaveformOptions` dataclass: `waveform_color`, `waveform_progress_color`, `trim_region_color`, `show_recording_waveform`, `skip_length`, `sample_rate` |
| **Streaming input** | Must have `"microphone"` in sources. `streaming=True` enables real-time mic → backend streaming |
| **Streaming output** | Function yields audio chunks; component plays them progressively |
| **Recording** | `recording=True` starts mic capture immediately; `start_recording`/`stop_recording` events |
| **Subtitles** | Supports `.srt`, `.vtt`, `.json` files, or list of `{"text": str, "timestamp": [start, end]}` dicts |
| **Editable** | `editable=True` shows waveform trim/selection controls |
| **Format** | `"wav"` (lossless) or `"mp3"` (compressed). Applies to both input conversion and output |

### Event Details

```python
audio.stream(fn, inputs, outputs)       # Fires continuously during mic recording
audio.change(fn, inputs, outputs)       # Value changed (upload, record, edit, clear)
audio.play(fn, inputs, outputs)         # Playback started
audio.pause(fn, inputs, outputs)        # Playback paused
audio.stop(fn, inputs, outputs)         # Playback stopped
audio.start_recording(fn, ...)          # Microphone recording started
audio.pause_recording(fn, ...)          # Recording paused
audio.stop_recording(fn, ...)           # Recording stopped
audio.upload(fn, inputs, outputs)       # File uploaded
audio.input(fn, inputs, outputs)        # User interacted (immediate, no debounce)
audio.clear(fn, inputs, outputs)        # Component cleared
```

### Streaming Output Pattern

```python
import numpy as np
import gradio as gr

def stream_audio():
    sample_rate = 22050
    duration = 2.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    for freq in range(220, 880, 110):
        chunk = np.sin(2 * np.pi * freq * t)
        yield (sample_rate, chunk.astype(np.float32))

with gr.Blocks() as demo:
    audio = gr.Audio(label="Streaming Tone", streaming=True)
    btn = gr.Button("Play")
    btn.click(stream_audio, None, audio)
```

### Data Flow

- **Input → Backend**: Converted to `(sample_rate, np.ndarray)` if `type="numpy"`, or file path if `type="filepath"`
- **Backend → Output**: Return `(sample_rate, np.ndarray)` for numpy output, or file path for filepath output
- **Streaming output**: Yield `(sample_rate, np.ndarray)` chunks — each appended to a growing buffer on frontend

## 2. gr.Video

### Constructor Parameters

```python
gr.Video(
    value: str | Path | Callable | None = None,
    *,
    format: str | None = None,           # e.g., "mp4", "avi"
    sources: list[Literal["upload", "webcam"]] | Literal["upload", "webcam"] | None = None,
    height: int | str | None = None,
    width: int | str | None = None,
    include_audio: bool | None = None,    # True for upload, False for webcam by default
    autoplay: bool = False,
    loop: bool = False,
    streaming: bool = False,              # Output streaming via .ts chunks
    buttons: list[Literal["download", "share"] | Button] | None = None,
    watermark: WatermarkOptions | None = None,
    subtitles: str | Path | list[dict[str, Any]] | None = None,
    playback_position: float = 0,
    webcam_options: WebcamOptions | None = None,
    # ... standard params
)
```

### Key Features

| Feature | Description |
|---------|-------------|
| **Format conversion** | Uses internal FFmpeg bindings (`ffmpy`) to convert. If output isn't browser-playable, auto-converts to h.264 mp4 |
| **Webcam recording** | `sources=["webcam"]` enables recording via browser MediaRecorder API |
| **Mirroring** | `webcam_options.mirror` flips webcam video horizontally |
| **Watermark** | `WatermarkOptions` with image file path and position |
| **Subtitles** | Same format as Audio: `.srt`, `.vtt`, `.json`, or dict list |
| **Audio controls** | `include_audio=True/False` to retain/remove audio track |
| **Streaming output** | Backend yields `.ts` files (MPEG-TS with h.264); frontend assembles into playable video |

### Event Details

```python
video.change(fn, inputs, outputs)       # Value changed
video.clear(fn, inputs, outputs)        # Cleared
video.play(fn, inputs, outputs)         # Playback started
video.pause(fn, inputs, outputs)        # Playback paused
video.stop(fn, inputs, outputs)         # Playback stopped (by user or ended)
video.end(fn, inputs, outputs)          # Video reached the end
video.start_recording(fn, ...)          # Webcam recording started
video.stop_recording(fn, ...)           # Webcam recording stopped
video.upload(fn, inputs, outputs)       # File uploaded
video.input(fn, inputs, outputs)        # User interacted
```

### Streaming Output Pattern

```python
import subprocess
import gradio as gr

def stream_video():
    # Simulate video chunks — each is a .ts segment
    for i in range(10):
        chunk_path = f"/path/to/segment_{i:03d}.ts"
        # ... generate chunk ...
        yield chunk_path

with gr.Blocks() as demo:
    video = gr.Video(label="Streaming", streaming=True)
    btn = gr.Button("Start")
    btn.click(stream_video, None, video)
```

### Browser Playability

For videos to play in-browser, use:
- `.mp4` with h.264 codec
- `.webm` with VP9 codec
- `.ogg` with Theora codec

If the backend returns a non-playable format, Gradio attempts auto-conversion to h.264 mp4 via FFmpeg. If conversion fails, the original file is returned as-is.

## 3. gr.Image

### Constructor Parameters

```python
gr.Image(
    value: str | PIL.Image.Image | np.ndarray | Callable | None = None,
    *,
    format: str = "webp",               # Output format for numpy/PIL values
    height: int | str | None = None,
    width: int | str | None = None,
    image_mode: str | None = "RGB",      # "1", "L", "RGB", "RGBA", "CMYK", etc.
    sources: list[Literal["upload", "webcam", "clipboard"]] | None = None,
    type: Literal["numpy", "pil", "filepath"] = "numpy",
    streaming: bool = False,             # Webcam streaming
    buttons: list[Literal["download", "share", "fullscreen"] | Button] | None = None,
    webcam_options: WebcamOptions | None = None,
    watermark: WatermarkOptions | None = None,
    placeholder: str | None = None,      # Custom upload prompt text
    # ... standard params
)
```

### Key Features

| Feature | Description |
|---------|-------------|
| **Multiple sources** | Upload from files, webcam capture, or clipboard paste |
| **Format selection** | Default output format `"webp"` for size efficiency. Supports any PIL format |
| **Streaming input** | Only works with `sources=["webcam"]`. Sends continuous webcam frames to backend |
| **Image mode** | PIL image mode for preprocessing: `"RGB"`, `"L"` (grayscale), `"RGBA"`, etc. |
| **Placeholder** | Custom text for drag-and-drop zone. Use `#` for heading |
| **Watermark** | Overlay image on displayed output (bottom-right, 10px inset) |
| **Buttons** | `"download"`, `"share"` (to HF Spaces), `"fullscreen"`, or custom `gr.Button()` |

### Event Details

```python
image.change(fn, inputs, outputs)       # Value changed
image.clear(fn, inputs, outputs)        # Cleared
image.stream(fn, inputs, outputs)       # Webcam streaming frames
image.select(fn, inputs, outputs)       # User clicked on the image (position data)
image.upload(fn, inputs, outputs)       # File uploaded/pasted/captured
image.input(fn, inputs, outputs)        # Immediate user interaction
```

### Streaming Input Pattern

```python
import numpy as np
import gradio as gr

def process_frame(img):
    # img is np.ndarray with shape (H, W, 3)
    return np.fliplr(img)  # Mirror horizontally

with gr.Blocks() as demo:
    img = gr.Image(sources=["webcam"], streaming=True)
    output = gr.Image()
    img.stream(process_frame, img, output, time_limit=30)
```

### Data Type Notes

| `type` | Input return | Output accept | Limitations |
|--------|-------------|---------------|-------------|
| `"numpy"` | `np.ndarray` shape `(H, W, 3)` uint8 0-255 | Same | No animated GIFs |
| `"pil"` | `PIL.Image.Image` | `PIL.Image.Image` or `np.ndarray` | Supports animated GIFs |
| `"filepath"` | `str` path to temp file | `str` path or URL | Supports SVG, animated GIFs |

## 4. gr.File

### Constructor Parameters

```python
gr.File(
    value: str | list[str] | Callable | None = None,
    *,
    file_count: Literal["single", "multiple", "directory"] = "single",
    file_types: list[str] | None = None,    # e.g. ['image', '.json', '.mp4']
    type: Literal["filepath", "binary"] = "filepath",
    height: int | str | float | None = None,
    allow_reordering: bool = False,
    buttons: list[Button] | None = None,
    # ... standard params
)
```

### Key Features

| Feature | Description |
|---------|-------------|
| **file_count** | `"single"` = one file; `"multiple"` = select multiple; `"directory"` = upload entire folder |
| **file_types** | Filter by category: `"image"`, `"audio"`, `"video"`, `"text"`, `"file"` (any), or by extension: `".json"`, `".py"`, etc. |
| **type** | `"filepath"` returns `NamedString` path; `"binary"` returns `bytes` |
| **Drag-reorder** | `allow_reordering=True` enables drag-to-reorder in file list |
| **Download event** | `Events.download` fires when user clicks a file to download |
| **Delete event** | `Events.delete` fires when user removes a file from the list |

### Event Details

```python
file.change(fn, inputs, outputs)        # File list changed
file.select(fn, inputs, outputs)        # A specific file was selected (returns index)
file.clear(fn, inputs, outputs)         # All files cleared
file.upload(fn, inputs, outputs)        # New file(s) uploaded
file.delete(fn, inputs, outputs)        # File removed from list
file.download(fn, inputs, outputs)      # File downloaded by user
```

### Return Values by Configuration

| `file_count` | `type` | Returns |
|-------------|--------|---------|
| `"single"` | `"filepath"` | `str` (path) |
| `"single"` | `"binary"` | `bytes` |
| `"multiple"` | `"filepath"` | `list[str]` |
| `"multiple"` | `"binary"` | `list[bytes]` |
| `"directory"` | `"filepath"` | `list[str]` |
| `"directory"` | `"binary"` | `list[bytes]` |

## 5. gr.Gallery

### Constructor Parameters

```python
gr.Gallery(
    value: Sequence[np.ndarray | PIL.Image.Image | str | Path | tuple] | Callable | None = None,
    *,
    format: str = "webp",
    file_types: list[str] | None = None,
    columns: int | None = 2,
    rows: int | None = None,
    height: int | float | str | None = None,
    allow_preview: bool = True,
    preview: bool | None = None,
    selected_index: int | None = None,
    object_fit: Literal["contain", "cover", "fill", "none", "scale-down"] | None = None,
    buttons: list[Literal["share", "download", "download_all", "fullscreen"] | Button] | None = None,
    type: Literal["numpy", "pil", "filepath"] = "filepath",
    fit_columns: bool = True,
    sources: list[Literal["upload", "webcam", "clipboard"]] | None = None,
    interactive: bool | None = None,
    # ... standard params
)
```

### Key Features

| Feature | Description |
|---------|-------------|
| **Mixed media** | Supports both images and videos in the same gallery |
| **Captions** | Pass as `(media, caption)` tuples — caption displayed below thumbnail |
| **Preview mode** | Click thumbnail to view full-size; `allow_preview` controls this |
| **Events** | `preview_open` / `preview_close` — unique to Gallery |
| **Grid layout** | `columns` and `rows` control grid; `height` triggers scrollbar overflow |
| **Buttons** | `"share"` (to HF Spaces), `"download"` (selected), `"download_all"`, `"fullscreen"` |
| **fit_columns** | If fewer items than columns, expand to fill width |
| **Object fit** | CSS `object-fit` for thumbnails: `"contain"`, `"cover"`, `"fill"`, `"none"`, `"scale-down"` |
| **File types** | Filter upload by file extension or category |

### Event Details

```python
gallery.select(fn, inputs, outputs)         # Clicked on media (returns index + caption)
gallery.upload(fn, inputs, outputs)         # New media uploaded
gallery.change(fn, inputs, outputs)         # Gallery contents changed
gallery.delete(fn, inputs, outputs)         # Media removed
gallery.preview_open(fn, inputs, outputs)   # Preview overlay opened
gallery.preview_close(fn, inputs, outputs)  # Preview overlay closed
```

### Return Value

As input: Returns `list[tuple[media, caption_or_None]]` where media type depends on `type` parameter.

As output: Pass `list` of file paths, numpy arrays, PIL images, or `(media, caption)` tuples.

## 6. gr.ImageEditor

### Constructor Parameters

```python
gr.ImageEditor(
    value: EditorValue | Callable | None = None,
    *,
    format: str = "webp",
    image_mode: str | None = "RGB",
    sources: list[Literal["upload", "webcam", "clipboard"]] | None = None,
    type: Literal["numpy", "pil", "filepath"] = "numpy",
    layers: bool = True,
    brush: Brush | None = None,
    eraser: Eraser | None = None,
    # ... standard params
)
```

### Key Features

| Feature | Description |
|---------|-------------|
| **Multi-layer editing** | `background` + multiple `layers` + computed `composite` |
| **Brush tool** | `Brush` dataclass: `default_size`, `colors`, `default_color`, `color_mode` ("fixed" or "defaults") |
| **Eraser tool** | `Eraser` dataclass: `default_size` (int or "auto") |
| **Return structure** | `EditorValue` TypedDict: `{"background", "layers", "composite"}` |
| **Apply event** | `Events.apply` fires when user clicks "Apply" in the editor |

### Data Model

```python
class EditorValue(TypedDict):
    background: ImageType | None     # Original uploaded image
    layers: list[ImageType]          # Drawn layers (brush strokes, shapes)
    composite: ImageType | None      # background + layers merged

# Control options
class Brush:
    default_size: int | Literal["auto"] = "auto"
    colors: list[str | tuple[str, float]] | None = None
    default_color: str | tuple[str, float] | None = None
    color_mode: Literal["fixed", "defaults"] = "defaults"

class Eraser:
    default_size: int | Literal["auto"] = "auto"
```

## Common Patterns & Pitfalls

### Streaming Pattern Comparison

| Component | Input Streaming | Output Streaming | Best For |
|-----------|----------------|------------------|----------|
| Audio | `streaming=True`, mic source | Yield `(sample_rate, chunk)` | Voice assistants, live transcription |
| Video | ✗ (recording, not stream) | Yield `.ts` chunk files | Live video generation |
| Image | `streaming=True`, webcam only | ✗ | Real-time camera filters, object detection |

### Media Format Handling

- **Audio**: Always prefer `"wav"` for lossless, `"mp3"` for smaller files. Format conversion happens on the backend via `pydub`.
- **Image**: Default output is `"webp"` — good balance of quality and size. Change to `"png"` for lossless, `"jpeg"` for photos.
- **Video**: Browser compatibility requires h.264 in `.mp4`. Gradio auto-converts non-compatible formats via bundled FFmpeg.

### Performance Tips

1. **Streaming audio/video**: Use server-side events; each chunk is sent progressively
2. **Gallery with many images**: Set `height` to enable scrolling; avoid loading 100+ items
3. **Image Editor**: `layers` uses more memory; keep image sizes reasonable (≤1024px)
4. **File uploads**: Large files → use Gradio's built-in chunked upload (automatic for files > 10MB)
5. **Webcam streaming**: Set `time_limit` on `.stream()` to prevent infinite streaming

### Theming Media Components

```python
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    # Audio waveform colors
    audio = gr.Audio(
        waveform_options=WaveformOptions(
            waveform_color="#ddd",
            waveform_progress_color="#6366f1",
            trim_region_color="#818cf8"
        )
    )
    # Image display
    img = gr.Image(height=400, width=600)
```

### Common Errors & Solutions

| Error | Cause | Fix |
|-------|-------|-----|
| `Audio streaming only available if sources includes 'microphone'` | `streaming=True` without mic source | Add `sources=["microphone"]` |
| `Image streaming only available if sources is ['webcam']` | `streaming=True` with multiple sources | Set `sources=["webcam"]` |
| Video won't play in browser | Wrong codec/container | Use `.mp4` with h.264, or let Gradio auto-convert |
| `Invalid file type` from File component | File doesn't match `file_types` filter | Remove or broaden `file_types` |
| Gallery images very small | `columns` too high | Reduce `columns` or set `fit_columns=True` |

## Version History

| Gradio Version | Changes |
|----------------|---------|
| 5.0 | Major media components rewrite; streaming support |
| 6.0 | Audio waveform editing, subtitles support |
| 6.5 | ImageEditor with brush/eraser tools |
| 6.10 | Gallery video support + preview events |
| 6.15 | File directory upload, `preview_close` event |
| 6.20 | WaveformOptions `sample_rate`, `playback_position` for Audio/Video |
