# HF Learnings — Gradio 6 Native Plot Components Deep Dive

## 2026-07-25: hf-gradio-6-native-plot-components — Gradio 6 Native Plot Components Complete Reference (Topic #351)

### Summary

Comprehensive deep dive into Gradio 6's native plot component family (`gr.LinePlot`, `gr.ScatterPlot`, `gr.BarPlot`, and the generic `gr.Plot`). These components provide declarative, DataFrame-backed charting with client-side rendering (built on Vega-Altair), eliminating the need for matplotlib/plotly for common use cases. All three share the **identical API** with over 20 dedicated parameters for axis configuration, color mapping, binning, aggregation, tooltips, and layout. Includes architecture overview, full API reference, usage patterns, event system, and integration patterns.

### Architecture

```
pandas DataFrame
     │
     ▼
 gr.LinePlot / gr.ScatterPlot / gr.BarPlot
     │
     ├── Client-side rendering (Svelte + Vega-Altair)
     ├── No server roundtrip for rendering
     ├── Built-in aggregation + binning
     └── Interactive tooltips, selection, zoom
     
gr.Plot (fallback)
     │
     ├── Server-side rendering
     ├── Accepts matplotlib / plotly / bokeh / altair figures
     └── Heavier, but supports arbitrary plots
```

**Key Design Decision:** Native plot components render **entirely on the client** using Vega-Altair declarative grammar. The server only sends the DataFrame (as JSON) + parameter config. This means:
- Zero server CPU for rendering
- Faster interactivity (pan, zoom, tooltips)
- Smaller payload than serialized matplotlib figures

### Component Comparison

| Feature | `gr.LinePlot` | `gr.ScatterPlot` | `gr.BarPlot` | `gr.Plot` |
|---------|:---:|:---:|:---:|:---:|
| Accepts DataFrame | ✅ | ✅ | ✅ | ❌ |
| Client-side render | ✅ | ✅ | ✅ | ❌ |
| Built-in binning/aggregation | ✅ | ✅ | ✅ | ❌ |
| Color series | ✅ | ✅ | ✅ | ❌ |
| Select/double-click events | ✅ | ✅ | ✅ | ❌ |
| Accepts matplotlib/plotly | ❌ | ❌ | ❌ | ✅ |
| Accepts callables | ✅ | ✅ | ✅ | ✅ |
| Accepts PlotData | ✅ | ✅ | ✅ | ✅ |

### Full API Reference

All three native plot components (`gr.LinePlot`, `gr.ScatterPlot`, `gr.BarPlot`) share exactly the same constructor parameters:

#### Data Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `value` | `pd.DataFrame \| Callable \| None` | `None` | DataFrame containing the data, or a callable returning one |
| `x` | `str` | *(required)* | Column name for the x-axis |
| `y` | `str \| list[str]` | *(required)* | Column name(s) for the y-axis (must be numeric) |
| `color` | `str \| None` | `None` | Column name to split into multiple colored series |

#### Label & Title Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `title` | `str \| None` | `None` | Chart title displayed on top |
| `x_title` | `str \| None` | `None` | X-axis title (defaults to x column name) |
| `y_title` | `str \| None` | `None` | Y-axis title (defaults to y column name) |
| `color_title` | `str \| None` | `None` | Color legend title (defaults to color column name) |

#### Binning & Aggregation Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `x_bin` | `str \| float \| None` | `None` | Grouping for x values. Numeric: bin size. Datetime: "1h", "15m", "10s", etc. |
| `y_aggregate` | `Literal['sum', 'mean', 'median', 'min', 'max']` | `None` | Aggregation function when x_bin is set or x is categorical |

#### Axis Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `x_lim` | `list[float \| None]` | `None` | [min, max] for x-axis. Use None to auto-scale one side. |
| `y_lim` | `list[float \| None]` | `None` | [min, max] for y-axis. Use None to auto-scale one side. |
| `x_label_angle` | `float` | `0` | X-axis label rotation (degrees clockwise) |
| `y_label_angle` | `float` | `0` | Y-axis label rotation (degrees clockwise) |
| `sort` | `str \| list[str]` | `None` | Sort order for categorical x: "x", "y", "-x", "-y", or explicit list |

#### Appearance Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `color_map` | `dict[str, str]` | `None` | Custom color mapping for series labels → CSS color strings |
| `tooltip` | `Literal['axis', 'none', 'all'] \| list[str]` | `'axis'` | Tooltip mode or list of columns to show |
| `height` | `int \| None` | `None` | Plot height in pixels |

#### Standard Gradio Component Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `label` | `str \| None` | `None` | Component label shown above the plot |
| `every` | `Timer \| float \| None` | `None` | Recalculate value on interval |
| `inputs` | `Component \| list \| None` | `None` | Inputs that trigger recalculation |
| `show_label` | `bool \| None` | `None` | Show/hide label |
| `container` | `bool` | `True` | Wrap in container with padding |
| `scale` | `int \| None` | `None` | Relative size in Row (integer) |
| `min_width` | `int` | `160` | Minimum pixel width |
| `visible` | `bool \| Literal['hidden']` | `True` | Visibility |
| `elem_id` | `str \| None` | `None` | HTML DOM id |
| `elem_classes` | `list[str] \| str \| None` | `None` | CSS classes |
| `render` | `bool` | `True` | Whether to render in Blocks context |
| `key` | `str \| int \| tuple \| None` | `None` | Identity key for gr.render() preservation |
| `preserved_by_key` | `list[str]` | `"value"` | Params preserved across re-renders |

### Event System

| Event | Description | Event Data |
|-------|-------------|------------|
| `.change()` | Triggered on value change (user or function update) | - |
| `.select()` | User selects/deselects the plot | `SelectData` (value=label, selected=bool) |
| `.double_click()` | User double-clicks the plot | - |

All events accept standard parameters: `fn`, `inputs`, `outputs`, `api_name`, `queue`, `batch`, `concurrency_limit`, `time_limit`, `trigger_mode`, `js`, `cancels`, etc.

### Usage Patterns

#### 1. Basic Line Plot

```python
import gradio as gr
import pandas as pd

df = pd.DataFrame({
    "month": ["Jan", "Feb", "Mar", "Apr"],
    "sales": [100, 150, 130, 200]
})

with gr.Blocks() as demo:
    gr.LinePlot(df, x="month", y="sales", title="Monthly Sales")

demo.launch()
```

#### 2. Multiple Series with Color

```python
import gradio as gr
import pandas as pd

df = pd.DataFrame({
    "week": [1, 2, 3, 4, 1, 2, 3, 4],
    "revenue": [100, 120, 110, 140, 80, 90, 95, 105],
    "region": ["US", "US", "US", "US", "EU", "EU", "EU", "EU"]
})

with gr.Blocks() as demo:
    gr.LinePlot(
        df,
        x="week",
        y="revenue",
        color="region",
        color_map={"US": "blue", "EU": "green"},
        title="Revenue by Region"
    )

demo.launch()
```

#### 3. Real-time Updating Plot

```python
import gradio as gr
import pandas as pd
import random

def get_data():
    return pd.DataFrame({
        "time": range(10),
        "value": [random.random() for _ in range(10)]
    })

with gr.Blocks() as demo:
    gr.LinePlot(get_data, x="time", y="value", every=1)

demo.launch()
```

#### 4. Bar Plot with Aggregation

```python
import gradio as gr
import pandas as pd

df = pd.DataFrame({
    "category": ["A", "A", "B", "B", "C"],
    "score": [10, 20, 30, 25, 15]
})

with gr.Blocks() as demo:
    # Groups by category, shows mean per category
    gr.BarPlot(df, x="category", y="score", y_aggregate="mean")

demo.launch()
```

#### 5. Scatter Plot with Axis Limits

```python
import gradio as gr
import pandas as pd

df = pd.DataFrame({
    "height": [1.5, 1.6, 1.7, 1.8, 1.9],
    "weight": [50, 60, 65, 75, 80],
    "gender": ["F", "F", "M", "M", "M"]
})

with gr.Blocks() as demo:
    gr.ScatterPlot(
        df,
        x="height",
        y="weight",
        color="gender",
        x_lim=[1.4, 2.0],
        y_lim=[40, 90],
        tooltip="all"
    )

demo.launch()
```

#### 6. Using gr.Plot for matplotlib (legacy figures)

```python
import gradio as gr
import matplotlib.pyplot as plt
import numpy as np

def make_plot():
    fig, ax = plt.subplots()
    x = np.linspace(0, 10, 100)
    ax.plot(x, np.sin(x))
    ax.set_title("Sine Wave")
    return fig

with gr.Blocks() as demo:
    gr.Plot(make_plot)

demo.launch()
```

#### 7. Interactive: Select Data Point

```python
import gradio as gr
import pandas as pd

df = pd.DataFrame({
    "city": ["NYC", "LA", "Chicago", "Houston"],
    "population": [8.4, 3.8, 2.7, 2.3]
})

with gr.Blocks() as demo:
    plot = gr.BarPlot(df, x="city", y="population")
    selected = gr.Label()
    
    def on_select(ev_data: gr.SelectData):
        return f"You selected: {ev_data.value}"
    
    plot.select(on_select, outputs=selected)

demo.launch()
```

### Key Insights

1. **All three share identical API** — `gr.LinePlot`, `gr.ScatterPlot`, and `gr.BarPlot` have the same constructor parameters. The only difference is the visual chart type. This means you can swap between them without changing any other code.

2. **Client-side rendering** — Unlike `gr.Plot` which serializes matplotlib/plotly figures on the server, native plots send the raw DataFrame (+ parameter config) to the browser, where Vega-Altair renders it. This is significantly faster and more bandwidth-efficient for repeated updates.

3. **Built-in aggregation is powerful** — `x_bin` + `y_aggregate` lets you summarize large datasets without preprocessing. For datetime x values, use string durations like `"1h"`, `"15m"`, `"10s"`. For numeric x, pass a bin size number.

4. **Categorical x sorting** — The `sort` parameter accepts `"x"` (ascending), `"-x"` (descending), `"y"` (by value ascending), `"-y"` (by value descending), or a list of explicit category names.

5. **Tooltip customization** — Use `tooltip="axis"` (default, shows axis values), `tooltip="all"` (shows all columns), `tooltip="none"` (hides), or a list of column names for custom tooltip content.

6. **Contrast with gr.Plot** — Use native plots when you have DataFrame data and need interactivity + performance. Use `gr.Plot` when you need: matplotlib/plotly/bokeh-specific features, subplots, annotations, or third-party charting libraries.

7. **No preprocessing needed** — Unlike the older pattern of using matplotlib within a function, native plots accept DataFrames directly. The `value` parameter can also be a callable (function) for dynamic updates.

8. **SelectData for interactivity** — `.select()` events pass `gr.SelectData` with `.value` (the label of the selected element) and `.selected` (boolean). This enables click-to-filter, drill-down, and other interactive patterns.

### Source Documentation

- Gradio Docs (v6.20.0): https://www.gradio.app/docs/gradio/lineplot
- Gradio Docs: https://www.gradio.app/docs/gradio/scatterplot
- Gradio Docs: https://www.gradio.app/docs/gradio/barplot
- Gradio Docs: https://www.gradio.app/docs/gradio/plot
- Creating Plots Guide: https://www.gradio.app/main/docs/gradio/creating-plots
- Time Plots Guide: https://www.gradio.app/main/docs/gradio/time-plots

### Demos

| Component | Demo Name |
|-----------|-----------|
| LinePlot | `line_plot_demo` |
| BarPlot | `bar_plot_demo` |
| ScatterPlot | `scatter_plot_demo` |
| Plot | `blocks_kinematics`, `stock_forecast` |
