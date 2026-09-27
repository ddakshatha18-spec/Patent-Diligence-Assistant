"""
Seed patent/abstract dataset for the Patent Diligence Assistant demo.

IMPORTANT: These are SYNTHETIC, illustrative abstracts written for this
prototype. They are not real patent filings and do not carry real
publication numbers. In a production build, this table would be replaced
by a licensed patent-search feed (e.g. USPTO PatFT/PPUBS, Google Patents
Public Datasets, or a paid clearance API) with real IDs and claims text.
"""

import uuid

def _pid():
    return f"seed-{uuid.uuid4().hex[:8]}"

SEED_PATENTS = [
    # ---- Domain: health / patient monitoring ----
    {
        "id": _pid(),
        "title": "Adaptive threshold alerting for continuous vital-sign streams",
        "abstract": (
            "A method for adjusting alert thresholds for heart rate, SpO2, and "
            "respiration data in real time based on a rolling baseline computed "
            "per patient, reducing false-positive alarms in remote monitoring "
            "settings while preserving sensitivity to acute deviation."
        ),
        "domain": "health",
        "source": "seed",
    },
    {
        "id": _pid(),
        "title": "Wearable fall-detection using accelerometer and gyroscope fusion",
        "abstract": (
            "A device and method that fuses tri-axial accelerometer and "
            "gyroscope signals through a state machine to distinguish a fall "
            "event from ordinary activity, triggering a caregiver notification "
            "after a configurable confirmation delay."
        ),
        "domain": "health",
        "source": "seed",
    },
    {
        "id": _pid(),
        "title": "Medication adherence inference from smart pill-bottle cap events",
        "abstract": (
            "A system that infers medication adherence by timestamping cap-open "
            "events on a smart pill bottle, comparing observed intervals to a "
            "prescribed schedule, and escalating a reminder through tiered "
            "channels (push, SMS, caregiver) when a dose is missed."
        ),
        "domain": "health",
        "source": "seed",
    },
    {
        "id": _pid(),
        "title": "Anomaly scoring for glucose time-series using local trend windows",
        "abstract": (
            "A method for scoring anomalies in continuous glucose monitor data "
            "by comparing short local trend windows against a patient-specific "
            "model, flagging both rapid excursions and slow drift patterns "
            "distinct from single-threshold alerting."
        ),
        "domain": "health",
        "source": "seed",
    },
    {
        "id": _pid(),
        "title": "Triage prioritization scoring from intake symptom checklists",
        "abstract": (
            "A scoring method that maps free-text and checklist symptom intake "
            "to an urgency tier using a weighted rule set, and routes the "
            "encounter to the appropriate clinical queue with an explainable "
            "breakdown of contributing factors."
        ),
        "domain": "health",
        "source": "seed",
    },
    # ---- Domain: disaster / emergency alerting ----
    {
        "id": _pid(),
        "title": "Geofenced push-alert dispatch prioritized by hazard proximity",
        "abstract": (
            "A method for dispatching emergency push notifications to devices "
            "within a dynamically computed geofence, ordering delivery by "
            "estimated hazard arrival time rather than registration order, to "
            "reduce time-to-notify for the highest-risk recipients first."
        ),
        "domain": "disaster-alert",
        "source": "seed",
    },
    {
        "id": _pid(),
        "title": "Multi-sensor flood-stage estimation with offline fallback",
        "abstract": (
            "A system that estimates flood stage from a combination of river "
            "gauge telemetry, satellite precipitation estimates, and "
            "crowd-sourced reports, and continues issuing best-effort alerts "
            "using cached models when connectivity to upstream sensors is "
            "lost."
        ),
        "domain": "disaster-alert",
        "source": "seed",
    },
    {
        "id": _pid(),
        "title": "Message deduplication across federated emergency alert feeds",
        "abstract": (
            "A method for merging emergency alert messages received from "
            "multiple independent authority feeds by clustering on hazard "
            "type, geographic overlap, and time window, so that end users "
            "receive a single deduplicated notification instead of repeated "
            "near-duplicate alerts."
        ),
        "domain": "disaster-alert",
        "source": "seed",
    },
    {
        "id": _pid(),
        "title": "Low-bandwidth mesh relay protocol for post-disaster messaging",
        "abstract": (
            "A store-and-forward relay protocol for short emergency messages "
            "over intermittent, low-bandwidth mesh links, prioritizing "
            "messages by a locally computed criticality score when link "
            "capacity is constrained."
        ),
        "domain": "disaster-alert",
        "source": "seed",
    },
    {
        "id": _pid(),
        "title": "Evacuation route re-scoring from live road-hazard reports",
        "abstract": (
            "A method that re-scores candidate evacuation routes in near real "
            "time as new road-hazard reports arrive, combining crowd-sourced "
            "and authority-sourced hazard reports into a single confidence-"
            "weighted routing graph."
        ),
        "domain": "disaster-alert",
        "source": "seed",
    },
]
