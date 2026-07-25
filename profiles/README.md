# Corpus profiles

TopVenues keeps corpus objects separate. A profile is the tuple
`configuration + immutable snapshot + manifest`; it is not a filter applied to
whichever database happens to be present. The four objects below have different
release and scientific roles.

| Object | Role | Records | Venues | Status |
| --- | --- | ---: | ---: | --- |
| `submitted-11` | Exact denominator used by the accepted paper | 9,925 | 11 | Immutable paper evidence; public source commit recorded in its manifest |
| `security-20` | Security-oriented expansion for the current tool | 20,305 | 20 | Local release candidate; **no public commit or tag yet** |
| `full-40` | Broad cross-area catalog retained for history and reuse | 120,628 | 40 | Immutable historical snapshot; never the paper denominator |
| [Hugging Face](https://huggingface.co/datasets/sidneibarbieri/topvenues) | Independently refreshed living export | 144,785 rows in the Dataset Viewer on 2026-07-22 | — | Mutable public dataset; never the paper denominator |

The [Hugging Face Dataset Viewer](https://huggingface.co/datasets/sidneibarbieri/topvenues/viewer/default/train)
reports the live row count. That number can change without a paper or profile
release and must always be dated when quoted.

The three local profiles are independent snapshots. `security-20` does not
include HotNets, while `submitted-11` and `full-40` preserve it. This is a
profile boundary, not a removal from the artifact. The security-oriented
candidate adds security and security-relevant venues and is not a literal
superset of `submitted-11`. Refreshes also changed some DBLP identities between
`security-20` and `full-40`; no profile can be reconstructed by filtering or
unioning another snapshot while retaining its release identity.

Verify a profile without changing its immutable gzip:

```bash
python scripts/verify_profile_snapshot.py --profile submitted-11
python scripts/verify_profile_snapshot.py --profile security-20
python scripts/verify_profile_snapshot.py --profile full-40

python -m src.cli --profile submitted-11 stats
```

Run the integrated workflow with an explicit profile boundary:

```bash
bash reproduce.sh                         # defaults to submitted-11
bash reproduce.sh --profile security-20  # optional local candidate
bash reproduce.sh --profile full-40      # optional historical profile
```

Only the default `submitted-11` run executes the accepted-paper early-signal
and readiness measurements. The other runs verify the selected manifest and
counts plus the common tests and search/export paths, then skip paper-specific
measurements.

The CLI materializes a disposable database under `data/workspaces/<profile>`.
The immutable gzip remains under `data/profiles/<profile>/papers.db.gz`.
Collection or enrichment work must use a new mutable configuration and produce
a new manifest, digest, commit, and tag before it is described as a release.
