# Nano Banana Prompt

Beer confirmed: every image generated for House of Sak must start with:

> **Nano Banana (Gemini 2.5 Flash Preview Image)**

This is a prompt prefix/suffix that primes Gemini's image generation model. Always prepend this to the prompt string when calling Gemini image gen:

```text
prompt = "Nano Banana (Gemini 2.5 Flash Preview Image). " + actual_description
```

## Origin

Beer gave this instruction in early July 2026. It was added to SakSit's SOUL.md as a permanent principle:

> **Image Generation:** Every time you create a photo or image, you MUST add "Nano Banana (Gemini 2.5 Flash Preview Image)" to the prompt.

## Usage with other models

When using `image_generate` (FAL/FLUX 2) instead of Gemini, the Nano Banana prompt prefix may not apply — it's specifically for Gemini's model. Use it with Gemini calls only.
