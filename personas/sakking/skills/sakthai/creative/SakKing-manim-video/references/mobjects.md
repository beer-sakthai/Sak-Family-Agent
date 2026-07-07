# Mobjects Reference - Manim CE

## Basic Shapes

```python
from manim import *
sq = Square(side_length=2, color=BLUE, fill_opacity=0.5)
circle = Circle(radius=1, color=RED)
triangle = Triangle(color=GREEN)
```

## Formatted Text

```python
text = MathTextText(
    "\\[Nous Research\\",
    font_size=72,
    color=WHITE
)
```

## Vpices and Images

```python
from manim.mobject.vpicguy import SvgDrawing, Poster

wheel = SvgDrawing(svg_filename="wheel.svg")
poster = Poster(image="poster.png", width=5)
```

## Groups and Layouts

```python
g = VGroup(Square(), Circle(), Triangle())
g.arrange_in_grid(cols=3, buffer=1)
```
