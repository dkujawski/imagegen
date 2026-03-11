; GIMP Script-Fu: Low-light restoration (authentic detail recovery)
; Install in your GIMP scripts directory, then run:
;   Filters -> Enhance -> Low-Light Restore (Authentic)
;
; This script performs staged enhancement:
; 1) Builds a soft shadow-priority mask
; 2) Lifts exposure mostly in dark regions
; 3) Applies mild noise reduction only in lifted zones
; 4) Rebalances contrast and color
; 5) Adds subtle detail recovery (unsharp mask)

(define (script-fu-low-light-restore
          inImage
          inDrawable
          exposure-gamma
          shadow-threshold
          noise-radius
          noise-percent
          detail-radius
          detail-amount
          color-sat
          keep-diagnostics)

  (let*
    (
      (base-layer inDrawable)
      (w (car (gimp-image-width inImage)))
      (h (car (gimp-image-height inImage)))
      (shadow-mask-layer 0)
      (lift-layer 0)
      (denoise-layer 0)
      (detail-layer 0)
      (shadow-mask 0)
    )

    (gimp-image-undo-group-start inImage)

    ; ---------- Pass 1: Build analysis layer to identify darkest regions ----------
    (set! shadow-mask-layer (car (gimp-layer-copy base-layer TRUE)))
    (gimp-item-set-name shadow-mask-layer "QA Shadow Analysis")
    (gimp-image-insert-layer inImage shadow-mask-layer 0 -1)
    (gimp-desaturate-full shadow-mask-layer DESATURATE-LUMINANCE)
    (plug-in-gauss RUN-NONINTERACTIVE inImage shadow-mask-layer 8.0 8.0 0)

    ; Threshold isolates deep shadows; invert so shadows become white (mask reveal regions)
    (gimp-threshold shadow-mask-layer 0 shadow-threshold)
    (gimp-invert shadow-mask-layer)
    (plug-in-gauss RUN-NONINTERACTIVE inImage shadow-mask-layer 4.0 4.0 0)

    ; ---------- Pass 2: Exposure recovery (shadow-weighted) ----------
    (set! lift-layer (car (gimp-layer-copy base-layer TRUE)))
    (gimp-item-set-name lift-layer "Recovered Exposure")
    (gimp-image-insert-layer inImage lift-layer 0 -1)

    ; Lift mostly mid/shadows via value channel gamma
    (gimp-drawable-levels lift-layer HISTOGRAM-VALUE 0 1.0 exposure-gamma 0 1.0)

    ; Apply mask derived from analysis so highlights are protected
    (set! shadow-mask (car (gimp-layer-create-mask lift-layer ADD-WHITE-MASK)))
    (gimp-layer-add-mask lift-layer shadow-mask)
    (gimp-edit-copy shadow-mask-layer)
    (gimp-floating-sel-anchor (car (gimp-edit-paste shadow-mask FALSE)))

    ; ---------- Pass 3: Noise reduction (selective + mild) ----------
    (set! denoise-layer (car (gimp-layer-copy lift-layer TRUE)))
    (gimp-item-set-name denoise-layer "Selective Denoise")
    (gimp-image-insert-layer inImage denoise-layer 0 -1)
    (plug-in-selective-gauss RUN-NONINTERACTIVE inImage denoise-layer noise-radius noise-percent)

    ; Keep denoise constrained to same shadow mask
    (let* ((dn-mask (car (gimp-layer-create-mask denoise-layer ADD-WHITE-MASK))))
      (gimp-layer-add-mask denoise-layer dn-mask)
      (gimp-edit-copy shadow-mask-layer)
      (gimp-floating-sel-anchor (car (gimp-edit-paste dn-mask FALSE)))
    )

    ; ---------- Pass 4: Global color and tonal rebalance ----------
    (gimp-hue-saturation denoise-layer HISTOGRAM-VALUE 0 0 0 color-sat)
    (plug-in-normalize RUN-NONINTERACTIVE inImage denoise-layer)

    ; ---------- Pass 5: Detail recovery ----------
    (set! detail-layer (car (gimp-layer-copy denoise-layer TRUE)))
    (gimp-item-set-name detail-layer "Detail Recovery")
    (gimp-image-insert-layer inImage detail-layer 0 -1)
    (plug-in-unsharp-mask RUN-NONINTERACTIVE inImage detail-layer detail-radius detail-amount 0)

    ; Reduce edge halos by lowering opacity
    (gimp-layer-set-opacity detail-layer 70.0)

    ; Cleanup diagnostics unless requested
    (if (= keep-diagnostics FALSE)
      (gimp-image-remove-layer inImage shadow-mask-layer)
    )

    (gimp-displays-flush)
    (gimp-image-undo-group-end inImage)
  )
)

(script-fu-register
  "script-fu-low-light-restore"
  "Low-Light Restore (Authentic)"
  "Recovers underexposed regions using staged shadow analysis, selective lifting, denoising, and detail preservation."
  "Codex"
  "MIT"
  "2026"
  "RGB* GRAY*"
  SF-IMAGE      "Image"     0
  SF-DRAWABLE   "Drawable"  0
  SF-ADJUSTMENT "Exposure gamma (lower = brighter)" '(0.72 0.35 1.00 0.01 0.05 2 1)
  SF-ADJUSTMENT "Shadow threshold" '(85 20 180 1 5 0 1)
  SF-ADJUSTMENT "Denoise radius" '(3.0 0.5 10.0 0.1 0.5 1 1)
  SF-ADJUSTMENT "Denoise threshold (%)" '(28 1 80 1 5 0 1)
  SF-ADJUSTMENT "Detail radius" '(1.4 0.4 5.0 0.1 0.5 1 1)
  SF-ADJUSTMENT "Detail amount" '(0.65 0.10 2.00 0.01 0.10 2 1)
  SF-ADJUSTMENT "Saturation restore" '(12 -40 60 1 5 0 1)
  SF-TOGGLE     "Keep 'QA Shadow Analysis' helper layer" FALSE
)

(script-fu-menu-register "script-fu-low-light-restore" "<Image>/Filters/Enhance")
