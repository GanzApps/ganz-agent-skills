---
name: "cloudflare-r2"
description: "Upload, download, and manage files in Cloudflare R2 storage. Use for media hosting, asset storage, and S3-compatible file operations."
---

# Cloudflare R2 Storage Skill

## Agent Prompt (Follow This)

When you need to use R2 storage:

1. **Read credentials from TOOLS.md** — Look for the R2 section under `### R2 URL Security` and credential blocks
2. **Never expose pub URLs in user-facing output** — Use Gumroad or platform-native hosting for public downloads
3. **Use S3 endpoint for API operations** — `https://a76e974e7c97043eb60c5a97bb651284.r2.cloudflarestorage.com`
4. **Use pub URL only for internal verification** — `https://pub-a7c94b0487c048c882d69ef4d0ab7a78.r2.dev/{key}`

### Before Uploading
- Check file size (R2 has no hard limit but keep < 100MB for performance)
- Determine correct ContentType (video/mp4, image/jpeg, etc.)
- Choose key path: `{project}/{date}/{filename}` for organization

### After Uploading
- Verify with `client.head_object()` — check ContentType and size
- Log the S3 URI: `s3://content-result/{key}`
- If user needs public download link → redirect to Gumroad or platform-native hosting

### Common Operations
```python
import boto3, mimetypes

# READ CREDENTIALS FROM TOOLS.md — do not hardcode in scripts
# Access Key ID: from TOOLS.md R2 section
# Secret Access Key: from TOOLS.md R2 section

client = boto3.client(
    's3',
    endpoint_url='https://a76e974e7c97043eb60c5a97bb651284.r2.cloudflarestorage.com',
    aws_access_key_id='[READ_FROM_TOOLS_MD]',
    aws_secret_access_key='[READ_FROM_TOOLS_MD]',
    region_name='auto'
)

# Upload
client.upload_file('/path/to/file.mp4', 'content-result', 'project/2026-05/file.mp4',
                   ExtraArgs={'ContentType': 'video/mp4'})

# Verify
head = client.head_object(Bucket='content-result', Key='project/2026-05/file.mp4')
print(f"Size: {head['ContentLength']}, Type: {head['ContentType']}")

# List
objs = client.list_objects_v2(Bucket='content-result', Prefix='project/2026-05/')
for o in objs.get('Contents', []):
    print(o['Key'], o['Size'])

# Delete
client.delete_object(Bucket='content-result', Key='project/2026-05/old-file.mp4')
```

## Shell Helpers (awscli)
```bash
# Configure once (credentials from TOOLS.md)
aws configure set aws_access_key_id [FROM_TOOLS_MD] --profile r2
aws configure set aws_secret_access_key [FROM_TOOLS_MD] --profile r2
aws configure set region auto --profile r2
aws configure set endpoint_url https://a76e974e7c97043eb60c5a97bb651284.r2.cloudflarestorage.com --profile r2

aws --profile r2 s3 cp /tmp/file.mp4 s3://content-result/project/2026-05/file.mp4
aws --profile r2 s3 ls s3://content-result/project/2026-05/
aws --profile r2 s3 rm s3://content-result/project/2026-05/old-file.mp4
```

## URL Security Rules (CRITICAL)
| URL Type | Use Case | Share Publicly? |
|----------|----------|----------------|
| `pub-*.r2.dev` | Internal verification only | ❌ NEVER |
| `*.r2.cloudflarestorage.com` | API access only | ❌ NEVER |
| Gumroad / platform native | User downloads | ✅ YES |

## Organization Convention
```
content-result/
  ├── {project-name}/
  │   ├── {YYYY-MM}/
  │   │   ├── {filename}
  │   │   └── ...
  │   └── ...
  └── temp/              # Temporary files, clean up after use
```

## Troubleshooting
- **403 Forbidden** → Check credentials in TOOLS.md, may need refresh
- **Slow upload** → Use multipart for files > 50MB
- **Wrong ContentType** → Always set `ExtraArgs={'ContentType': '...'}`
- **Public access denied** → Pub URLs are intentionally restricted, use platform hosting
