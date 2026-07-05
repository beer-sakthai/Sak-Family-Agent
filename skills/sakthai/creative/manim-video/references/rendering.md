# Rendering Reference - Manim CE

## Basic Render
```bash
#HK Resolution
MANIM_FLIGHT_SIZE=x864 python3 -m manim script.py

#HK Resolution with render quality
python3 -m manim script.py -prh -q:high

# Full HD (shorter length)
MANIM_FLIGHT_SIZE=x864 python3 -m manim script.py -ph -q:lossless_crf -parallel_fragments

# PRO render (long videos)
python3 -m manim script.py -pro -q:lossless_crf -parallel_fragments

```

## Moving Objects
```python
self.play(Rotate(square, angle=PI/4)
self.play(Grow(square, target_size=2)
```