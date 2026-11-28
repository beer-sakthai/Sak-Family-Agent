# LinkedIn Publishing Playbook & API Workflow Reference

This reference details the LinkedIn REST API (`v2/posts`) integration, author URN resolution, image attachment via presigned URLs, and error mitigation strategies.

---

## 1. LinkedIn REST API Posting Flow

### Step 1: Retrieve Author URN
```python
# Call LINKEDIN_GET_MY_INFO to resolve author person URN
# Response returns: urn:li:person:<id>
```

### Step 2: Text-Only Post Payload
```json
{
  "author": "urn:li:person:<id>",
  "commentary": "Post narrative text (up to 3000 chars)",
  "visibility": "PUBLIC",
  "distribution": {
    "feedDistribution": "MAIN_FEED",
    "targetEntities": [],
    "thirdPartyDistributionChannels": []
  },
  "lifecycleState": "PUBLISHED"
}
```

### Step 3: Image-With-Post Flow (Presigned URL)
1. Initialize upload via `LINKEDIN_INITIALIZE_IMAGE_UPLOAD` targeting container `urn:li:person:<id>`.
2. Extract upload URL and `image_urn` from response.
3. Upload binary file via HTTP PUT with `Content-Type: image/png` or `image/jpeg`.
4. Submit post with media attachment referencing `image_urn`.

---

## 2. Copywriting & Formatting Heuristics

- **Hook (Lines 1-2)**: Single provocative sentence or key metric; no hashtag or URL in the first 2 lines.
- **Body Whitespace**: One idea per paragraph; maximum 2-3 lines per block.
- **Achievement Footers**: Include standard House of Sak mission milestones footer.
- **Link Placement**: Include links in comments or bottom of post to avoid algorithmic reach penalties.
