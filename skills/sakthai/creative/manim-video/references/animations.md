# Animations Reference - Manim CE

## Basic Animations
```python
from manim import *
sq = Square()
self.play(Show(Square()))
self.play(Wait(sq, 1))                    # Wait for 1 second
self.play(FadeIn(sq, 0.5))                # Fade in over 0.5s
self.play(Grow(sq, 1))                   # Grow to factor 2*self.play(Transform(sq, sq.copy().scale(0.5).next_to(UR\n, LEFT\\n by 2, UP by 1))) # Move
```

## Creation Order and Layers
```python
sq = Square()
circle = Circle()

self.add(sq)
self.add(circle)
# Now the behavior is different: sq is behind circle
self.clear()

self.add(circle)
self.add(sq)
# Now sq is in front of circle
```

\u0638\u0646\u0648\u0627\u0645 \u0627\u0644\u0627\u0631\u0627\u0628 - \u0627\u0644\u0627\u0631\u0627\ua000