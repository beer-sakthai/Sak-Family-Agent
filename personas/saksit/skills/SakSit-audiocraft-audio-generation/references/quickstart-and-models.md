# AudioCraft Quickstart, Model Architecture & Generation Reference

This reference details the installation, model variants, generation parameters, melody conditioning, and audio export recipes for Meta's AudioCraft (MusicGen, AudioGen, EnCodec).

---

## 1. Quickstart & Installation

```bash
uv pip install audiocraft torch torchaudio
```

### Basic Text-to-Music (MusicGen)
```python
import torchaudio
from audiocraft.models import MusicGen

model = MusicGen.get_pretrained("facebook/musicgen-small")
model.set_generation_params(duration=10)  # Generate 10 seconds

descriptions = ["lo-fi hip hop beat with smooth piano and mellow drums"]
wav = model.generate(descriptions)  # [1, 1, 320000]

torchaudio.save("output.wav", wav[0].cpu(), sample_rate=32000)
```

---

## 2. Model Family Overview

| Model | Checkpoint | Size | Capabilities |
|:---|:---|:---:|:---|
| **MusicGen Small** | `facebook/musicgen-small` | 300M | Fast text-to-music generation |
| **MusicGen Medium** | `facebook/musicgen-medium` | 1.5B | Richer harmonic detail |
| **MusicGen Melody** | `facebook/musicgen-melody` | 1.5B | Text + melodic audio prompt conditioning |
| **AudioGen Medium** | `facebook/audiogen-medium` | 1.5B | Text-to-sound effects and Foley |

---

## 3. Melody Conditioning Pattern

```python
melody, sr = torchaudio.load("whistle.wav")
wav = model.generate_with_chroma(
    descriptions=["cinematic orchestral theme"],
    melody_wavs=melody[None],
    melody_sample_rate=sr,
)
```
