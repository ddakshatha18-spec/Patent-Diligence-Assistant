"""Sample module for the Patent Diligence Assistant demo.

Contains one function deliberately phrased to closely echo a seed patent
abstract (fall detection via sensor fusion), to prove Subagent A's
similarity scan actually fires on the demo dataset.
"""


def detect_fall_event(accel_samples, gyro_samples, confirm_delay_s=5):
    """Fuse accelerometer and gyroscope signals through a state machine to
    distinguish a fall event from ordinary activity, and trigger a
    caregiver notification after a configurable confirmation delay.
    """
    state = "idle"
    impact_detected = any(abs(s) > 2.5 for s in accel_samples)
    orientation_change = any(abs(g) > 120 for g in gyro_samples)

    if impact_detected and orientation_change:
        state = "possible_fall"

    if state == "possible_fall":
        # wait confirm_delay_s before escalating, to filter out false positives
        return {"state": "confirming", "delay_s": confirm_delay_s}

    return {"state": "idle"}


def _clamp(value, lo, hi):
    # trivial boilerplate helper — should NOT get flagged by Subagent A
    return max(lo, min(hi, value))


def format_vitals_summary(heart_rate, spo2, resp_rate):
    """Format a plain-language summary string of vital signs for the
    on-call dashboard.
    """
    return f"HR {heart_rate} bpm, SpO2 {spo2}%, resp {resp_rate}/min"


def dedupe_alert_batch(alerts):
    """Cluster incoming emergency alert messages by hazard type, rough
    geographic overlap, and time window so a single merged notification is
    sent instead of several near-duplicate pushes to the same device.
    """
    seen = {}
    merged = []
    for alert in alerts:
        key = (alert.get("hazard_type"), round(alert.get("lat", 0), 1), round(alert.get("lon", 0), 1))
        if key not in seen:
            seen[key] = alert
            merged.append(alert)
    return merged
