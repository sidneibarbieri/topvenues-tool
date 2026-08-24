# Immutable profile

This repository preserves three immutable profiles:

| Profile | Records | Venues | Role |
| --- | ---: | ---: | --- |
| `security-20` | 20,305 | 20 | Frozen SBSeg-SF artifact profile |
| `security-20-v2` | 14,863 | 20 | Deduplicated successor for current researcher workflows |
| `security-20-v3` | 14,859 | 20 | Strict-window, identity-adjudicated current release |

The profile configuration declares the venue keys and target years. Its manifest declares the compressed snapshot SHA-256 and observed data counts. Validate it with:

```bash
python scripts/verify_profile_snapshot.py --profile security-20
python scripts/verify_profile_snapshot.py --profile security-20-v2
python scripts/verify_profile_snapshot.py --profile security-20-v3
```

A refreshed scope is a new profile and release, not an in-place change to this snapshot.
