# CI Verification Method — Don't Guess, Check

Beer corrected this session: "If I said it not check, dont guess." The following is the correct method for checking CI status on `beer-sakthai/Sak-Family-Agent`.

## Wrong Method (what failed)

Checking the commit's `status` endpoint (`/commits/<SHA>/status`) returns "pending" even when all checks pass. This is NOT reliable.

Checking workflow runs via `/actions/runs?per_page=5` shows completed runs but misses in-progress ones and can miss the latest commit.

## Correct Method

Query the **check-runs API** for the latest commit on main:

```python
import urllib.request, json

# Step 1: Get the latest commit SHA
resp = urllib.request.urlopen("https://api.github.com/repos/beer-sakthai/Sak-Family-Agent/commits/main")
sha = json.load(resp)["sha"]

# Step 2: Get check runs for that SHA
url = f"https://api.github.com/repos/beer-sakthai/Sak-Family-Agent/commits/{sha}/check-runs"
resp = urllib.request.urlopen(url)
d = json.load(resp)

# Step 3: Evaluate each check
for c in d.get("check_runs", []):
    name = c["name"]
    conclusion = c.get("conclusion", "in_progress")
    # "success" = passed, "failure" = failed, None = still running

# Step 4: Count failures
fails = [c for c in d["check_runs"] if c.get("conclusion") == "failure"]
print(f"Failures: {len(fails)}")
```

## Key Points

- A "pending" commit status does NOT mean failure — it means some checks are still running
- Always check the check-runs list directly
- Report actual check states, not guesses
- If you see "pending" without any checks listed, query the check-runs API for the specific commit SHA — it may have been a different commit than the one you were checking
