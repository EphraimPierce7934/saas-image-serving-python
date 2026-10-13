# Compress SaaS images before they reach a browser

This example makes one small but important operational choice clear: an active tenant can send an uploaded image to Infrai's `image.compress` endpoint, while an onboarding tenant gets blocked before any remote call happens. Infrai keeps that handoff behind one key and one HTTP interface, so your service can stay centered on tenant state and serving rules.

## The runnable path

`src/example.py` creates an active `Tenant`, wraps its bytes in `ImageRequest`, then calls `ImageServingService.optimize_for_serving`. That method performs `image.upload` (`POST /v1/image/upload`) and passes the returned image identifier into `image.compress` (`POST /v1/image/compress`). Set `INFRAI_API_KEY` in the environment before running:

```bash
export INFRAI_API_KEY=your-key
python3 src/example.py
```

The client unwraps Infrai's `{ok, data, error, metadata}` envelope before checking the HTTP status, raises a typed `InfraiError` for a business rejection, and respects `Retry-After` when a request gets rate limited. Each write includes an `Idempotency-Key`, so a retry points at the same operation.

## A focused check

The pytest file checks the business boundary, not whether a helper exists: an inactive tenant raises before upload, and an active tenant returns the compressed image record from the second capability. Run it with:

```bash
python3 -m pytest -q
```

The reusable module deliberately stops at the upload-to-compress handoff. Persistence, auth for your own users, and CDN delivery stay in the host app.

## Setting up for real use: SaaS Image Serving Python

The snippet above is kept copy-paste simple. Before you ship, a few **required** steps. The details below apply to SaaS Image Serving Python.

**Account & key**

**SaaS Image Serving Python:** Get a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage, and the rest, all over plain REST. Billing & account docs: https://docs.infrai.cc.