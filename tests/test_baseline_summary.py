"""Regression tests for call-level baseline accounting."""

import math

from evaluation.baseline_validation.run_live_baselines import (
    summarize_operation,
    summarize_service,
)


def test_batches_are_one_logical_request_and_metering_tracks_attempts() -> None:
    batch_rows = [
        {
            "s2_operation": "doi_batch",
            "s2_status": 200,
            "s2_match": True,
            "s2_has_abstract": index < 142,
        }
        for index in range(143)
    ]
    batch_calls = [
        {
            "operation": "doi_batch",
            "items": 143,
            "status": 200,
            "latency_ms": 1236.9,
            "attempts": 2,
        }
    ]

    service = summarize_service("s2", batch_calls, batch_rows)
    operation = summarize_operation("s2", "doi_batch", batch_calls, batch_rows)

    assert service["http_200_n"] == 1
    assert service["logical_http_requests"] == 1
    assert service["network_attempts_including_retries"] == 2
    assert service["doi_batch"] == operation
    assert operation["sample_n"] == 143
    assert operation["record_match_n"] == 143
    assert operation["abstract_n"] == 142
    assert operation["http_status"] == 200
    assert operation["batch_wall_latency_ms"] == 1236.9

    title_rows = [
        {
            "openalex_operation": "title_search",
            "openalex_status": 200 if index < 54 else 400,
            "openalex_match": index < 28,
            "openalex_has_abstract": index < 22,
        }
        for index in range(57)
    ]
    title_calls = [
        {
            "operation": "title_search",
            "items": 1,
            "status": 200 if index < 54 else 400,
            "latency_ms": 500 + index,
            "attempts": 2 if index == 0 else 1,
            "server_reported_api_budget_metering_usd": (0.002 if index == 0 else 0.001),
            "metered_network_attempts": 2 if index == 0 else 1,
        }
        for index in range(57)
    ]

    title = summarize_service("openalex", title_calls, title_rows)

    assert title["http_200_n"] == 54
    assert title["logical_http_requests"] == 57
    assert title["network_attempts_including_retries"] == 58
    assert title["metered_network_attempts"] == 58
    assert title["metering_completeness"] == "complete"
    assert title["title_search"]["http_400_n"] == 3
    assert math.isclose(title["server_reported_api_budget_metering_usd"], 0.058, rel_tol=1e-12)
