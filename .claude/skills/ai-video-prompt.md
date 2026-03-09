# Skill: AI Video Prompt Engineer

Generate optimized prompts tailored to the specific model and workflow being used in Flashboards / AI Yaro Flasher.

## Input
Always ask the user for:
1. **Model** — Which model? (e.g., Kling, Wan, Hunyuan, Minimax, Runway, Pika, Sora, LTX, CogVideo, etc.)
2. **Workflow** — What type? (text2vid, img2vid, vid2vid, lip sync, face swap, upscale, etc.)
3. **Scene description** — What should happen in the video?
4. **Style** — Cinematic, commercial, anime, hyper-realistic, raw/organic, etc.
5. **Camera movement** — Static, pan, zoom, dolly, orbit, drone, handheld
6. **Duration** — 5s / 10s / 15s
7. **Reference** (optional) — Any input image or video?

## Process
1. **Tailor the prompt to the exact model** — each model has different strengths, syntax preferences, and keywords it responds to. Research or ask about the model's quirks if unsure.
2. **Tailor to the workflow** — img2vid prompts describe motion/change from the input image. Text2vid prompts need full scene description. Vid2vid prompts focus on style transfer or modifications.
3. Include: subject, action, environment, lighting, camera, style, mood
4. Provide a negative prompt if the model supports it
5. Give 2-3 prompt variations (safe, creative, experimental)
6. Note any model-specific settings to adjust (CFG scale, steps, motion strength, etc.)

## Model-Specific Notes
Build this section over time as you learn what works for each model. Update this file after discovering what produces good results.

| Model | Best For | Prompt Style | Key Tips |
|-------|----------|-------------|----------|
| *(to be filled as you use models)* | | | |

## Output
Save to `outputs/prompts/` with filename format: `{model}-{workflow}-{description}.md`

## Mandatory Rules
- **Always end every prompt with "No CGI look."** — All outputs must look hyper-realistic, not synthetic or rendered.
- **Always write for fast-paced, high-energy motion** — snappy cuts, rapid movement, aggressive transitions. No slow or floaty motion unless specifically asked.
- **Always include unique/creative camera movements** — avoid basic static or simple pan. **Never repeat the same camera combo twice in a row across prompts.** Randomly mix and combine from this pool each time:
  - **1st Person POV:** GoPro chest mount, helmet cam, eye-level handheld, over-the-shoulder, POV run/fall/jump, hands-in-frame perspective
  - **3rd Person:** FPV drone chase, orbiting tracking shot, dolly zoom reveal, over-the-shoulder follow, side-profile speed track
  - **Dynamic moves:** whip pan, crash zoom, barrel roll, FPV drone dive, Dutch angle tracking, vertigo effect, overhead slam down, through-object pass, 360 orbit snap, low-angle power shot, reverse pull-out, snap tilt, canted angle whip, underpass slide
  - Always combine 2-3 different movements within a single clip for variety
- Use natural lighting, real-world physics, organic motion, and photographic texture in descriptions
- Avoid words like "3D render", "digital art", "animated" unless specifically requested

## Tips
- Front-load the most important details
- Be specific about lighting (golden hour, neon, studio, natural)
- Specify camera lens when possible (35mm, 85mm, wide angle)
- Include motion keywords the model responds to
- Different models interpret the same prompt differently — always tailor
