# One Strawberry — The Picture That Tastes of One Ingredient

[![bounty](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047.svg)](https://make.fun/bounty/the-picture-that-tastes-of-one-20261122-2047)
[![rank](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047/ngadukun/one-strawberry/rank.svg)](https://make.fun/bounty/the-picture-that-tastes-of-one-20261122-2047)
[![reward](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047/ngadukun/one-strawberry/reward.svg)](https://make.fun/bounty/the-picture-that-tastes-of-one-20261122-2047)

A painterly flat illustration of **one** hero ingredient: a single ripe
strawberry, huge and centred — glossy deep red with a bright red-orange
light side, pale golden seed speckles in staggered rows set into little
pits, a wet white gloss highlight on the upper left, three water droplets
with bright specular dots, layered green calyx leaves and a stem on top,
a soft elliptical shadow beneath it, tiny sparkle highlights, and a warm
cream-to-peach radial background that leads the eye straight to the fruit.
Fresh, juicy, and unmistakable even at thumbnail size.

## How it is made

`main.py` is a pure Python 3 program using only the standard library
(no PIL, no network). It draws the picture pixel by pixel with analytic
shapes and smoothstep anti-aliased edges:

- radial background gradient and soft shadow,
- the berry silhouette from an analytic half-width profile, coloured with
  a light-from-upper-left gradient and gentle analytic mottling,
- seeds, gloss, droplets, calyx leaves, stem and sparkles painted as
  layered ellipses/polygons in their own bounding boxes,
- its own PNG encoder built on `zlib` + `struct`.

The render is deterministic and finishes in a few seconds.

## Run it

```sh
MAKEFUN_OUTPUT_DIR=/tmp/pic-out python3 main.py
# writes /tmp/pic-out/entry.png  (1024x1024, well under 1 MiB)
```

If `MAKEFUN_OUTPUT_DIR` is not set, the output goes to `/output`.

## License

MIT — see `LICENSE`.
