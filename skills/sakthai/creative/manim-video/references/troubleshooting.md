# Troubleshooting Reference - Manim CE

## Common Errors

### Error: `ModuleNotFoundError: No module named 'manim'`
- Missing Manim CE installation
- Run `pip install manim`

### Error: `Error: Unable to render as pdf export passes through things`
- You are mixing Manim pdf with other render profiles. Specify a single rendering method.
 - Use -pk and -pd parameters correctly

### Error: `Connection refused by server response: Not Open (opens error) during live streaming`
- Missing codecs (FFMpeg)
 - Run `pip install ffmpeg`

### Video renders as blank screen
- Forgot to add elements to the scene
- The animation ended immediately
- There's an error in your animation logic