from datetime import datetime
from typing import List, Dict
import json
import os
from app.config import VIOLATION_THRESHOLD
# In-memory violation log (resets on restart)
# In production you'd use PostgreSQL
violation_log: List[Dict] = []


class AlertSystem:

    def __init__(self, violation_threshold: int = 1):
        """
        violation_threshold: how many violations before alert fires
        """
        self.threshold = violation_threshold

    def check_and_log(self, summary: dict, source: str = "image") -> dict:
        """
        Check if summary has violations.
        Log it. Return alert if threshold exceeded.
        """
        if summary["total_violations"] >= self.threshold:
            alert = {
                "alert_id": f"ALT_{len(violation_log)+1:04d}",
                "timestamp": summary["timestamp"],
                "source": source,
                "violations": summary["violations"],
                "total_violations": summary["total_violations"],
                "severity": self._get_severity(summary["total_violations"])
            }
            violation_log.append(alert)
            return alert

        return None

    def _get_severity(self, count: int) -> str:
        if count >= 5:
            return "CRITICAL"
        elif count >= 3:
            return "HIGH"
        elif count >= 1:
            return "MEDIUM"
        return "NONE"

    def get_violation_log(self, limit: int = 50) -> List[Dict]:
        """Return recent violations, newest first."""
        return list(reversed(violation_log[-limit:]))

    def get_statistics(self) -> dict:
        """Overall violation statistics."""
        if not violation_log:
            return {
                "total_alerts": 0,
                "no_hardhat": 0,
                "no_vest": 0,
                "no_mask": 0
            }

        no_hardhat = sum(
            a["violations"].get("NO-Hardhat", 0)
            for a in violation_log
        )
        no_vest = sum(
            a["violations"].get("NO-Safety Vest", 0)
            for a in violation_log
        )
        no_mask = sum(
            a["violations"].get("NO-Mask", 0)
            for a in violation_log
        )

        return {
            "total_alerts": len(violation_log),
            "no_hardhat": no_hardhat,
            "no_vest": no_vest,
            "no_mask": no_mask,
            "most_common": max(
                [("NO-Hardhat", no_hardhat),
                 ("NO-Safety Vest", no_vest),
                 ("NO-Mask", no_mask)],
                key=lambda x: x[1]
            )[0]
        }


# Singleton instance
alert_system = AlertSystem(violation_threshold=VIOLATION_THRESHOLD)   