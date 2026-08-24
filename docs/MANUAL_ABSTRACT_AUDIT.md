# Manual abstract audit

The `security-20-v3` coverage count is exhaustive, but abstract quality requires
human comparison with publisher or repository evidence. Results from another
snapshot cannot be transferred to v3.

Generate the fixed venue-stratified sample:

```bash
python scripts/manual_abstract_audit.py \
  --profile security-20-v3 \
  --sample-size 200 \
  --output security-20-v3-manual-audit.csv
```

For every row, open `source_url`, compare the displayed source with `abstract`,
and enter `yes` or `no` in all three fields:

- `label_complete`: the abstract is complete rather than truncated;
- `label_uncontaminated`: navigation, copyright, references, or unrelated text
  are absent;
- `label_matches_paper`: the abstract belongs to the sampled title.

Record the reviewer identity or code and a short note for every negative label.
Do not infer labels from string length or another automated heuristic: that would
not be a manual validation.

Summarize a completed sheet:

```bash
python scripts/manual_abstract_audit.py \
  --summarize security-20-v3-manual-audit.csv
```

The summarizer reports the usable fraction and a 95% Wilson interval. Partially
labelled rows are reported as incomplete and excluded; they are never silently
treated as positive or negative. Commit labels only after the protocol has been
completed and independently checked.
