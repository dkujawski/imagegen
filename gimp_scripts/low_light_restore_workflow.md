# Low-light restoration workflow (GIMP + optional OpenCV/ImageMagick)

## Install the GIMP script
1. Copy `gimp_scripts/low_light_restore.scm` into your user scripts folder.
   - Linux: `~/.config/GIMP/2.10/scripts/`
   - Windows: `%APPDATA%\GIMP\2.10\scripts\`
   - macOS: `~/Library/Application Support/GIMP/2.10/scripts/`
2. Restart GIMP (or use **Filters → Script-Fu → Refresh Scripts**).
3. Open image, then run **Filters → Enhance → Low-Light Restore (Authentic)**.

## Human-in-the-loop tuning (recommended)
- Start with defaults.
- If image remains too dark: lower **Exposure gamma** gradually (e.g., `0.72 -> 0.66`).
- If highlights blow out: raise **Shadow threshold** (limits lift to deeper shadows).
- If grain appears: increase **Denoise threshold** slightly; avoid heavy radius.
- If skin or foliage looks dull: raise **Saturation restore** by +3 to +8.
- If halos appear: reduce **Detail amount** or **Detail radius**.

## Multi-pass strategy for severely dark photos
1. First pass at conservative values and keep diagnostics enabled.
2. Inspect `QA Shadow Analysis` layer to verify that only dark regions are selected.
3. Re-run the script with adjusted threshold and gamma.
4. Optional third pass only for color rebalance and detail refinement.

## Optional companion tools (open-source)
- **OpenCV** (`opencv-python`) for precomputing edge/shadow maps and face-region masks.
- **ImageMagick** for external linearization and channel statistics before entering GIMP.
- **face_recognition** or **dlib** for optional face-priority protection masks (avoid over-denoising facial details).
- **scikit-image** for non-local means denoise previews and comparison metrics.

## Optional ImageMagick pre-pass example
Use this before GIMP when shadows are extremely crushed:

```bash
magick input.jpg \
  -colorspace RGB \
  -channel RGB -sigmoidal-contrast 4,45% +channel \
  -evaluate multiply 1.12 \
  -brightness-contrast 5x8 \
  prepass.png
```

Then open `prepass.png` in GIMP and run the Script-Fu.
