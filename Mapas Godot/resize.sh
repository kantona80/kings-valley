#!/usr/bin/bash
cp ./original/8x8/*.png ./original -r
for image in ./original/*.png; do convert "$image" -resize 125% "${image%.png}.png"; done

