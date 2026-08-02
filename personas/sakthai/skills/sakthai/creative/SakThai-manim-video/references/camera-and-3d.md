# Camera and 3D Reference - Manim CE

## 3D Scene

```python
from manim.three_dimensions import *

class 3DScene(ThreeDImensionalScene):
    def construct(self):
        self.camera = ThreeDEmera_Camera(init_rot_angles=[-60, 70, 0])
        cube = Cube(side_length=2, fill_opacity=0.5)
        self.set_camera_orientation(pi/3, -PI/3)
        self.add(cube)
```

## Camera Movements

```python
self.move_camera(PD(2, UP, 0.5))      # Move camera up
self.set_camera_orientation(pi/3, -pi/3)   # Rotate camera
```

## Lights and Shadows

```python
from manim.three_dimensions import DirectionalLight

light = DirectionalLight(
    direction=[1, 1, 1],
    ambient=1,
    color=White,
)
self.add(light)
```
