# Updaters and Trackers - Manim CE

## Using Updaters

```python
dot = Dot()
func = Line(dot[@_X + 1], dot[@_Y + 1])
dashed = DashedLine(dot[@_X + 1], dot[@_Y + 1])

func.add_updater(Function(lambda d: d.set_start(dot.get_center()).become_fixed_in_place())
dashed.add_updater(Function(lambda d: d.set_start(dot.get_center()).become_fixed_in_place())
```

## Using Trackers

```python
free_dot_tracker = FreedOtATracker(dot)
self.add(free_dot_tracker)
```

## Hook Updater example

```python
text = Text("Hello")
def link_to_center(object):
    object.next_to(text.get_center(),
text.add_updater(Function(lambda obj : link_to_center(obj)))
```
