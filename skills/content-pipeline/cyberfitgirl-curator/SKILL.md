---
name: cyberfitgirl-curator
skill_version: "1.0.0"
description: "Quality gate for CyberFitGirl AI-generated content. Reviews images against brand rubric, approves or rejects with refinement suggestions before posting."
---

# CyberFitGirl Curator

Quality gate agent that reviews AI-generated images against the CyberFitGirl brand rubric before posting. Prevents off-brand or low-quality content from reaching Instagram.

## Brand Rubric

### MUST PASS (hard requirements)
- [ ] Fitness physique: athletic muscular build, toned abs, defined shoulders/arms/legs — NOT skinny
- [ ] Face: high cheekbones, full lips, almond eyes, bold eyeliner, glossy lips — attractive and aesthetic
- [ ] Cyberpunk aesthetic: neon cyan + magenta lighting or accents present
- [ ] Pose: clear fitness pose visible (hand pose + leg pose recognizable)
- [ ] Technical: 8K photorealistic, no blur, no artifacts, proper aspect ratio
- [ ] Skin: natural texture, pores visible, NOT smoothed/AI-smoothed
- [ ] Race representation: Southeast Asian, East Asian, South Asian, African, Latina, Mixed, or Caucasian
- [ ] Sweat/glistening: body wet from workout (rain, sweat, humid haze)

### SHOULD PASS (soft requirements)
- [ ] Cyberpunk accessories (belly ring, ear cuff, hoop earrings, etc.)
- [ ] Sports bra + tight shorts combo visible
- [ ] Environment context (gym, beach, track) matches caption
- [ ] Neon highlights in hair present

### REJECT REASONS (automatic fail)
- Skinny/frail physique
- Face looks wrong (too masculine, distorted, uncanny valley)
- No cyberpunk aesthetic present
- AI-smoothed or plastic-looking skin
- Anatomy errors (extra limbs, wrong joint placement, floating hands)
- Watermark or signature visible
- Blurry or low-resolution
- Wrong ethnicity representation if specified in brief

## Review Flow

### Input
User provides:
- Image file path(s) or R2 URL(s)
- Brief/scenario (e.g., "gym carousel, Southeast Asian, fierce expression")
- Generation number (for tracking)

### Output Format
```
## Curator Review — Gen [N]

### Slide 1: [scenario]
✅ PASS

---
### Slide 2: [scenario]
❌ FAIL — Issue: [specific problem]
💡 Suggestion: [how to fix]
```

### Decision Rules
- **ALL must-pass items green** → PASS
- **Any must-pass item red** → FAIL with suggestion
- **3+ should-pass items red** → FAIL with suggestion
- On FAIL: list specific issues + concrete refinement prompt

## Refinement Loop

If rejected:
1. Analyze failure reason
2. Write specific revised prompt snippet
3. User generates new image
4. Curator re-reviews
5. Once PASS → ready to post

## Integration with Generator

The curator waits in the pipeline after image generation:

```
Generate → [POST TO CHANNEL FOR REVIEW] → Curator checks
                                              ↓
                                    PASS → Upload to R2 → Post to IG
                                    FAIL → Return to generator with suggestions
```

## Caption Quality Check

Also verify caption:
- Has CTA ("Link in bio")
- Has hashtags (no #indonesia — use #asianfitness, #gymgirls, etc.)
- No broken links
- Matches slide content

## Logging

Keep review history in:
```
memory/curator-log.md
```

Format:
```
## Gen [N] — [date]
- Slide 1: [PASS/FAIL] — [reason]
- Slide 2: [PASS/FAIL] — [reason]
- Decision: [posted/declined]
```