# Decorations Reference - Manim CE

## Surrounding elements
```python
square = Square()
surrounding_rect = SurroundingRect(square)
box = Box(square)
```

## Arrows
```python
label = Text("Label")
arrow = Arrow(label, square, buffer_ratio=0.2)
```

## Braces
```python
angular_brace = AngularBrace(
    inner_radius=0.2,
    angle=PI/2,
    color=BLUE
)
linear_brace = LinearBrace(
    height=1.5,
    color=RED
)
```

## Frames
```python
square = Square()
label = Text("Framed").next_to(square.get_center())
frame = FRAme(square)
```