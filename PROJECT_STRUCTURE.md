# TopVenues — Project Structure

The repository is organized around three purposes: the runnable tool,
the curated research artifact, and active paper workspaces.

## Runtime Artifact

| Path | Purpose |
|------|---------|
| `src/` | collection, enrichment, persistence, export, CLI |
| `web/` | Streamlit interface |
| `tests/` | pytest coverage for core behavior |
| `profiles/<profile>/config.yaml` | closed configuration for each named corpus profile |
| `data/profiles/submitted-11/` | 9,925-record immutable paper denominator and manifest |
| `data/profiles/security-20/` | 20,305-record local release candidate and manifest; no public tag/commit yet |
| `data/profiles/full-40/` | 120,628-record immutable historical snapshot and manifest |
| `data/dataset/papers.db.gz` | default development snapshot; byte-identical to `security-20`, not the paper denominator |
| `data/dataset/papers.db.gz.sha256` | expected hash for the default development snapshot |
| `config.yaml` | mutable default configuration for the `security-20` candidate |
| `scripts/` | reproducibility, claim verification, ad-hoc maintenance |
| `Dockerfile`, `docker-compose.yml` | reproducible execution environment |
| `reproduce.sh` | end-to-end reproduction of `submitted-11` by default; other named profiles require `--profile` |

## Evaluation Documents

| Path | Purpose |
|------|---------|
| `README.md` | primary entry point for users |
| `ARTIFACT_README.md` | artifact overview for evaluation |
| `REVIEWER_GUIDE.md` | how to verify each headline claim |
| `profiles/README.md` | release boundary among the three local profiles and the living Hugging Face export |

The public [Hugging Face dataset](https://huggingface.co/datasets/sidneibarbieri/topvenues)
is not stored under `data/profiles/`. It is an independently refreshed living
export (144,785 Dataset Viewer rows on 2026-07-22) and never supplies the
accepted paper's denominator.

## Paper Workspaces

Manuscript drafts live under `papers/`, a local writing workspace that is
excluded from the public artifact so the released code and corpus remain
independent of any specific manuscript or venue.
