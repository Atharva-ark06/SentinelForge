"""Fail CI on explicitly disallowed dependency license families."""

import json
import subprocess
import sys


def check(packages):
    blocked = []
    for package in packages:
        licenses = package.get("License", "").upper()
        # LGPL is reported for review, but not prohibited by this GPL/AGPL gate.
        if ("AGPL" in licenses or "GPL" in licenses and "LGPL" not in licenses):
            blocked.append((package["Name"], licenses))
    return blocked


if __name__ == "__main__":
    result = subprocess.run([sys.executable, "-m", "piplicenses", "--format=json"],
                            capture_output=True, text=True, check=True)
    violations = check(json.loads(result.stdout))
    for name, license_name in violations:
        print(f"Disallowed license: {name}: {license_name}")
    if violations:
        sys.exit(1)
    print("Dependency license gate passed")
