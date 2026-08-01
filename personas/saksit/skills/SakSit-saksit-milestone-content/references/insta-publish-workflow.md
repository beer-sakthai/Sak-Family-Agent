# Instagram Publish Workflow

Two-step process for posting milestone content to Instagram:

## Step 1: Create Container
```
INSTAGRAM_POST_IG_USER_MEDIA
Arguments: {ig_user_id, caption, image_file: {name, mimetype, s3key}}
```
Returns `creation_id`.

## Step 2: Publish
```
INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH
Arguments: {ig_user_id, creation_id, max_wait_seconds: 60}
```

## Key Rules
- Omit `media_type` for feed posts (auto-infers as IMAGE)
- For Stories: pass `media_type: "STORIES"`
- Use s3key from `GOOGLEDRIVE_DOWNLOAD_FILE` → extract from s3url path
- Every feed post = Story too (Beer's rule)
