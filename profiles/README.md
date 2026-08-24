# Immutable profile

This release ships one immutable profile:

| Profile | Records | Venues | Role |
| --- | ---: | ---: | --- |
| `security-20` | 20,305 | 20 | Frozen SBSeg-SF artifact profile |
| `security-20-v2` | 14,863 | 20 | Deduplicated successor for current researcher workflows |

The profile configuration declares the venue keys and target years. Its manifest declares the compressed snapshot SHA-256 and observed data counts. Validate it with:

```bash
python scripts/verify_profile_snapshot.py --profile security-20
python scripts/verify_profile_snapshot.py --profile security-20-v2
```

A refreshed scope is a new profile and release, not an in-place change to this snapshot.
