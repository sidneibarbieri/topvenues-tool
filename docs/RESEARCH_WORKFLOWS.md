# Research workflows and tier policy

## 1. Map a topic's reference venues

Select **Security Big Four (Tier 1)** in Search or Insights. In TopVenues this
means only ACM CCS, IEEE S&P, USENIX Security, and NDSS. Search the topic,
inspect the records, and export the defensible subset.

Use this for orientation, reference mapping, and monitoring a narrow elite-venue
stream. It is not a claim that work outside those venues is unimportant.

## 2. Find recurring authors without overstating the result

In Insights, choose a topic and select `Any author`, `First author`, or `Last
author`, then apply a tier scope. Open an author's records before treating the
rank as actionable. The score is a transparent corpus-visibility heuristic; it
does not measure citation impact, quality, seniority, or identity-resolved
individuals.

## 3. Build a systematic-review candidate set

Start with **All declared venues** unless the review protocol justifies a
restriction. Apply topic, year, paper-class, and abstract-availability filters,
then export the resulting candidate set. Record every scope choice with the
snapshot identifier; TopVenues fixes the denominator but does not decide
relevance or inclusion.

## Tier policy

| Research-facing scope | Included venue tier(s) |
| --- | --- |
| Security Big Four (Tier 1) | ACM CCS, IEEE S&P, USENIX Security, NDSS |
| Tier 1 plus regional editions | Big Four plus ACM ASIA CCS and IEEE EURO S&P |
| Other top-tier venues | Explicit `top-tier` mapping in `src/tiers.py` |
| Strong venues | Explicit `strong` mapping in `src/tiers.py` |
| Survey journals | ACM Computing Surveys, IEEE Communications Surveys & Tutorials, Foundations and Trends in Privacy and Security |
