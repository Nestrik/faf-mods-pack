# Meshy chassis — retexture, 17 November 2026

`chassis_repaint.glb` is the delivered textured model; `chassis_repaint_albedo.png` is its embedded 2048×2048 albedo. `chassis_original.glb` preserves the user attachment. Geometry and original UV accessor bytes are identical; the mesh still has 1500 triangles. No game unit files were replaced.

Imagegen created the two source artwork images, `wheel_strip.png` and `armor_projection.png`. Prompt summaries: flat diffuse strip with six blue-gray painted wheels on charcoal metal; blue-gray top armor texture with rear hatches and grilles, broad panel seams, subtle wear and front lamp panels. Blender projects these images onto the hull and sides and bakes them into the original UV map. The original blurry normal and packed material maps are disconnected; the final material uses metallic 0.25, roughness 0.72 and the new albedo.

Build: run `bake_repaint.py` with local Blender, then `package_glb.py` with Python. The packaging script embeds the new PNG while preserving geometry data bytes. `verify_import.py` reimports the packaged GLB and renders `final_perspective.png` and `final_side.png`. Blender repeat import succeeded. The existing irregular side geometry and distorted surfaces remain visible, especially under lighting; texture alone does not flatten them. In-game appearance has not been checked.
