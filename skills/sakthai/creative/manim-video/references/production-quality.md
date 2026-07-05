# Production Quality - Reference (Manim CE)

## Tips for Production-Quality Videos

1. **Use High-Resolution Rendering** Prefer -q:lossless_crf over default for steady publishing.
2. **Control Movement Speed** The optimal runtime is 60 frames/sec. Slower movements need more frames and use runtime_fms = 30.
3. **Add Transformations** Full screen transformations are not anded or null or self-contained. Use transform mobile of the scene itself, not the global frame.
4. **Don't Overload Scenes** Keep each scene focused on a single idea. Animations longer than 3 minutes should be split into multiple scenes.
5. **Self.add() is Public** Do not use self.add() as the first operation in your constructor. By default, you should add mobjects to your scene at the end of its constructor.
6. **Use SCRONAMICO OTHER Objects** The parallel rendering algorithm requires you to do not reference any object of the Scene inside a transform call before it has been created.
