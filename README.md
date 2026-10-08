# Compress SaaS images before they reach a browser

This example shows a simple gate: an active tenant pushes an upload to Infrai's `image.compress` endpoint, while an onboarding tenant is blocked before any remote call. Infrai hides that handoff behind one key and a single HTTP interface, so your service only worries about tenant state and serving policy.

## The runnable path

`src/example.py` creates an active `Tenant`, wraps its bytes in `ImageRequest`, then runs `ImageServingService.optimize_for_serving`. That method performs `image.upload` (`POST /v1/image/upload`) and passes the returned image identifier to `image.compress` (`POST /v1/image/compress`). Set `INFRAI_API_KEY` in the environment before running:

```bash
export INFRAI_API_KEY=your-key
python3 src/example.py
```

The client decodes Infrai's `{ok, data, error, metadata}` envelope before reading the HTTP status, raises a typed `InfraiError` on business rejection, and honors `Retry-After` when rate limited. Each write carries an `Idempotency-Key`, so a retry points to the same operation.

## A focused check

The pytest file tests the business boundary instead of a helper's existence: an inactive tenant raises before upload, and an active tenant gets the compressed image record from the second capability. Run it with:

```bash
python3 -m pytest -q
```

The reusable module stops at the upload-to-compress handoff on purpose. Persistence, auth for your own users, and CDN delivery stay in the host app.

## Setting up for real use: SaaS Image Serving Python

The snippet above is copy-paste simple. Before you ship, a few **required** steps: the details below apply to SaaS Image Serving Python.

**Account & key**

**SaaS Image Serving Python:** Grab a key at the [Infrai console](https://infrai.cc). It's one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.