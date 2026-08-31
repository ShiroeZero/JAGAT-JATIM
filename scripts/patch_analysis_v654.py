"""Compatibility wrapper for the JAGAT V6.5.4 remediation.

Kept under the historical filename so older workflow references do not break.
The implementation lives in patch_analysis_v654_fix.py and is intentionally
idempotent.
"""
from patch_analysis_v654_fix import main


if __name__ == "__main__":
    main()
