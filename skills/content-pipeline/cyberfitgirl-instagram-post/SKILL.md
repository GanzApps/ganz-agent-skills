---
name: cyberfitgirl-instagram-post
skill_version: "1.1.0"
description: "Post CyberFitGirl content to Instagram. Handles carousel creation, caption with CTAs, and publishing workflow for the @cyber_fitgirl account."
---

# CyberFitGirl Instagram Post Skill

## Account Info
- **Username:** @cyber_fitgirl
- **IG User ID:** 26393714730330929
- **Account Type:** MEDIA_CREATOR
- **Bio Link:** https://cyberfitgirl.gumroad.com/l/freecyberfitgirl

## Prompt Library

### MODULAR PROMPT v3 — CyberFitGirl Athletic (2026-05-22)
```
fitness model photography,
<variable race> woman,
athletic muscular build (toned abs, defined shoulders, strong arms and legs),
NOT skinny,
<variable skin> skin,
high cheekbones, full lips, almond eyes,
attractive, beautiful, aesthetic,
<vary hair color> hair with neon cyan and magenta highlights,
bold eyeliner winged eyes,
glossy lips,
<vary expression> expression,
<variable hand pose> hand pose,
<variable leg pose> leg pose,
<variable camera angle> camera,
<vary Bra colour> <vary Bra texture> sports bra and <vary tight colour> <vary tight texture> tight fitting shorts,
sport wear aesthetic,
<vary list of accessories>,
body glistening with sweat,
pores visible,
natural skin texture NOT smoothed,
ULTRA DETAILED 8K PHOTOREALISTIC,
neon cyan + magenta cyberpunk lighting from sides,
<variable environment>,
<vary weather>
```

**Variable Swaps:**
| Variable | Options |
|---------|--------|
| `<variable race>` | Southeast Asian, East Asian, South Asian, African, Latina, Caucasian, Mixed |
| `<variable skin>` | caramel tan, olive, deep brown, fair, bronze, golden beige |
| `<vary hair color>` | black, dark brown, auburn (keep neon highlights constant) |
| `<vary expression>` | relaxed smile, fierce intensity, peaceful closed eyes, confident smirk |
| `<variable hand pose>` | hands behind head, arms crossed, hands on hips, arms extended |
| `<variable leg pose>` | deep squat wide stance, standing tall, lunge pose, sitting |
| `<variable camera angle>` | low angle, eye level, high angle, Dutch angle, close up face |
| `<vary Bra colour>` | white, black, neon pink, neon cyan, blush rose, red, electric blue |
| `<vary Bra texture>` | lace, cotton, silk, mesh/net, compression stretch, matte, glossy |
| `<vary tight colour>` | black, white, neon pink, neon cyan |
| `<vary tight texture>` | compression stretch, matte, glossy, cotton |
| `<variable accessories>` | belly button piercing silver ring, ear cuff, nose ring, ankle bracelet, layered gold chain necklace, hoop earrings, statement rings |
| `<variable environment>` | cinematic gym neon tubes, tropical beach sunset ocean, outdoor jogging track golden hour cityscape |
| `<vary weather>` | rain falling water droplets, dry natural sweat glistening, post-workout sweaty, humid haze |

### Example Compositions:
**Gym Carousel (3 slides):**
1. Gym | Southeast Asian | caramel tan | black hair | fierce expression | hands on hips | low angle
2. Beach | East Asian | fair skin | dark brown hair | relaxed smile | arms extended | eye level
3. Track | Mixed | bronze | black hair | confident smirk | arms crossed | close up

### PREMIUM PROMPT (Pinned Reference — 2026-05-21)
```
fitness model photography, Southeast Asian woman, athletic muscular build toned abs defined shoulders strong arms and legs, NOT skinny, caramel tan skin, high cheekbones, full lips, almond eyes, black hair with neon cyan and magenta highlights, bold eyeliner winged eyes, glossy lips, relaxed closed eyes peaceful smile, hands behind head facing camera, deep squat pose feet wide stance, wearing BLUSH ROSE lace triangle top with thin spaghetti straps, belly ring jewelry, TIGHT FITTED minimal black bottom hugging skin, body wet from rain, water droplets on skin glistening, neon cyan magenta cyberpunk lighting from sides, rain falling, ultra detailed 8k photorealistic, pores visible, natural skin texture not smoothed, athletic bodybuilder physique not skinny
```
Reference image: https://pub-a7c94b0487c048c882d69ef4d0ab7a78.r2.dev/cyberfitgirl/test/athletic_variant.png

## Project Context (CRITICAL)
- **Category:** Digital product (wallpaper packs)
- **Product:** Cyberpunk fitness aesthetic wallpapers
- **Monetization:** Gumroad sales (free sample → paid full pack)
- **Instagram Purpose:** Drive traffic to Gumroad, NOT motivation content
- **CTA Strategy:** "Link in bio" → free sample → email capture → upsell
- **Tone:** Aesthetic-first, product-focused, subtle FOMO
- **Target:** Indonesian & Asian women representation

## Pre-Flight Checklist
1. Check quota: `INSTAGRAM_GET_IG_USER_CONTENT_PUBLISHING_LIMIT`
2. Verify images are uploaded to R2 (public URLs, no query params)
3. Confirm caption includes CTA + hashtags (no "#indonesia")
4. Ensure bio link is active

## Posting Flow

### Step 1: Create Image Containers (Carousel)
For each image in carousel:
```
INSTAGRAM_POST_IG_USER_MEDIA
- ig_user_id: 26393714730330929
- image_url: <R2_PUBLIC_URL>  (must be https, no query params)
- is_carousel_item: true
```
Store each returned `id` as container_id.

### Step 2: Create Parent Carousel Container
```
INSTAGRAM_POST_IG_USER_MEDIA
- ig_user_id: 26393714730330929
- media_type: CAROUSEL
- children: [container_id_1, container_id_2, ...]  (2-10 items)
- caption: <caption_text>
```
Store returned `id` as creation_id.

### Step 3: Publish
```
INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH
- ig_user_id: 26393714730330929
- creation_id: <creation_id>
- max_wait_seconds: 60
```

### Step 4: Verify
```
INSTAGRAM_GET_IG_MEDIA
- ig_media_id: <published_media_id>
- fields: id,media_type,permalink,timestamp
```

## Caption Template
```
Neon. Sweat. Steel.

CyberFitGirl wallpapers — now featuring [ethnicity] athletes.

5 free in the sample pack. 33 in the full collection.

Representation matters. Aesthetic is universal.

🔥 Link in bio — grab the free pack.

#cyberpunk #fitnessaesthetic #wallpaper #[ethnicity]fitness #gymgirls #digitalart #cyberfitgirl #neon #representationmatters
```

## Image Requirements
- Aspect ratio: 9:16 (vertical)
- Format: JPG or PNG
- Source: MiniMax image-01 model
- Upload to: Cloudflare R2 (content-result bucket)
- Public URL format: `https://pub-a7c94b0487c048c882d69ef4d0ab7a78.r2.dev/<filename>`

## R2 Upload Script
```python
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
import boto3

client = boto3.client(
    's3',
    endpoint_url='https://a76e974e7c97043eb60c5a97bb651284.r2.cloudflarestorage.com',
    aws_access_key_id='05b2e3150cd11bc3cd01c009c2b95633',
    aws_secret_access_key='4bf03e3ac8142c7b78ba21cd85fedf1037be3bc9b28c4af6fdbf27751e8c99b2',
    region_name='auto'
)

client.upload_file(
    '/path/to/local/image.jpg',
    'content-result',
    'image_filename.jpg',
    ExtraArgs={'ContentType': 'image/jpeg'}
)

print('https://pub-a7c94b0487c048c882d69ef4d0ab7a78.r2.dev/image_filename.jpg')
```

## Quota & Limits
- Daily publish limit: 100 posts
- Carousel: 2-10 images
- Rate limit: 25 API-published posts per day (rolling)

## Verification
After publishing, check:
```
INSTAGRAM_GET_IG_MEDIA
- ig_media_id: <published_id>
- fields: id,media_type,permalink,timestamp
```
Expected: `media_type: IMAGE` or `CAROUSEL`, valid permalink

## Troubleshooting
| Issue | Fix |
|-------|-----|
| 400 error on image_url | Ensure URL is public, direct, no query params |
| Container timeout | Increase max_wait_seconds to 120 |
| Quota exceeded | Wait for rolling window reset |
| MediaBuilder error | Use INSTAGRAM_GET_POST_STATUS for unpublished containers |

## First Post Reference
- **Post ID:** 18101355800098001
- **Permalink:** https://www.instagram.com/p/DYadz3nFNrs/
- **Date:** 2026-05-16
- **Type:** Carousel (3 slides)
- **Images:** Indonesian fitness, Asian fitness, CTA slide

## Changelog
- **1.1.0** (2026-05-21): Added premium athletic prompt with Southeast Asian features, pinned in #cyberfitgirl channel