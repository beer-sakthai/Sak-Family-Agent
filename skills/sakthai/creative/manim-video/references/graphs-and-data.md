# Graphs and Data Reference - Manim CE

## Bar graph
```python
from manim import *
from manim.graphing import BarChart, BarLabel

colors = [Blue, Green, Yellow, Red, Purple]
data = [5, 4, 7, 3, 6]
bars = VGroup(
    BarChart(data, bar_configuration={"width":0.6}),
    BarLabel(5, 4, 7, 3, 6)
)
bars.set_color_by_value(colors)
self.add(bars)
```

## Line graph
```python
from manim.graphing import LineGraph

axes = Axes()
line_graph = LineGraph(
    points=[(-3, 4), (-2, 1), (-1, -2), (0, 0), (1, 2), (2, 3), (3, 5)],
    color=Blue,
)
axes.plot(line_graph)
self.add(axes)
```

## Pie Chart
```python
from manim.graphing import PieChart

pie_chart = PieChart(
    values=[30, 25, 20, 15],
    color=[Blue, Green, Yellow, Red]
)
self.add(pie_chart)
```