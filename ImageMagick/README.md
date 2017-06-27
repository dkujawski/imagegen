Generate a bunch of images for testing.
Requires a recent install of ImageMagick: www.imagemagick.org

`gen_script.bash` and `gen_all.bash` are the control scripts which collect parameters to execute pre baked scripts that use Imagemagick's `convert` script to generate images.

To generate one 256x256 size image for each script use:
```
./gen_all.bash 256 1 ./out
```
This will genarate a single 256x256 image for each script, putting the images in a directory `./out`
```
./out
├── fractal_colour_contours_256_1
│   └── 1.png
├── fractal_colour_contours-256_256_1
│   └── 1.png
├── fractal_filaments_256_1
│   └── 1.png
├── fractal_plasma_256_1
│   └── 1.png
├── fractal_swirl_256_1
│   └── 1.png
├── hextile_lines_256_1
│   └── 1.png
└── noise_paint_areas_256_1
    └── 1.png
```

To generate 30 images at 512x512 using the fractal_swirl script use:
```
./gen_script.bash 512 30 ./out ./scripts/fractal_swirl.bash
```
This will generate thirty images in the `./out` directory:
```
./out
├── fractal_swirl_512_30
│   ├── 01.png
│   ├── 02.png
│   ├── 03.png
│   ├── 04.png
│   ├── 05.png
│   ├── 06.png
│   ├── 07.png
│   ├── 08.png
│   ├── 09.png
│   ├── 10.png
│   ├── 11.png
│   ├── 12.png
│   ├── 13.png
│   ├── 14.png
│   ├── 15.png
│   ├── 16.png
│   ├── 17.png
│   ├── 18.png
│   ├── 19.png
│   ├── 20.png
│   ├── 21.png
│   ├── 22.png
│   ├── 23.png
│   ├── 24.png
│   ├── 25.png
│   ├── 26.png
│   ├── 27.png
│   ├── 28.png
│   ├── 29.png
│   └── 30.png

```

