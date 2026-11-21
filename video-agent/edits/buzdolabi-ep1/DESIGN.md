# Buzdolabındaki Hayat — Design

## Style Prompt
A warm, comic soap opera set inside a fridge at night. Flat 2D cartoon characters (rounded shapes,
thick dark outlines, big expressive eyes) live on glass shelves under cold blue moonlight. When the
door opens the whole world floods with warm white light — that light is the threat ("Büyük Işık").
The camera behaves like a soap-opera camera: slow push-ins on whoever speaks, dramatic zooms on
reactions, a frozen frame for the cliffhanger. Turkish captions are big, bouncy and readable.

## Colors
- Night (fridge closed): `#0f1b33` deep blue, ambient `#2a4a7a`
- Fridge walls: `#dcecf6` icy white-blue, shelf glass `#a9d4ee` with `#ffffff` highlights
- Big Light (door open): `#fff7e0` warm white
- Accent / drama: `#ff4d6d` soap-opera pink-red
- Outline / ink: `#1d1b2f`
- Character colours: Kemal cheese `#ffcf3f`, Nuri pickle `#6aa84f`, Yeliz yogurt `#fffdf7` + lid `#ff8fb1`,
  Arda avocado `#2f6b2f` / flesh `#c5e384` / seed `#8b5a2b`, Kâmil ketchup `#e0262c`, eggs `#fff3e0`

## Typography
- Titles and name chips: Fredoka 700
- Captions: Nunito 900 (white with thick ink stroke), narrator lines in Nunito 800 italic, light blue

## Motion
- Camera: `power2.inOut` 0.7–1.2 s moves; slow push-ins `sine.inOut`
- Characters: idle bob (sine), blinks every few seconds, mouth flaps on vowels from the TTS alignment
- Reactions: `back.out` pops, `elastic.out` for surprise, shakes for panic
- Door open: dark overlay drops to 0, warm white flash, bloom

## What NOT to Do
- No realistic food or brand logos (generic, unbranded products only)
- No captions below 1600 px (Reels UI covers the bottom)
- No emoji glyphs (the render machine may not have an emoji font)
- No pure black backgrounds except the very last fade
- No text smaller than 36 px
