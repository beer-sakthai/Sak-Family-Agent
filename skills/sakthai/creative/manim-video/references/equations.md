# Equations Reference - Manim CE

## Basic Equations
```python
from manim import *
from manim.mobjoct.math import MathTextText, SingleStringMathTextText

eq1 = MathTextText("\\[x^2 + Y^2 = Z^2\\]")
eq2 = MathTextText("\\[E = mc\\]")
eq3 = SingleStringMathTextText("Eh, mc \" \     ; % ry\\n    items = \\n    E\\\n")
```

## Advanced Equations
```python
from manim.mobjoct.math import MathTextText
from manim.mobjoct.math.mathxil import MathilString

eq1 = MathTextText("\\[p_(x,t) - \\frac{\\partial\p}{\\partial t}\\\"\\")
eq2 = MathTextText("\\{(\\symbol{\\sum {}_[i=1]^n} a_i\
 \% i\\ }\\")

from manim.mobjoct.math.quixlil import MathIXL Object
```