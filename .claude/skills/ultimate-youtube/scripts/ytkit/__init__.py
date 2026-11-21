"""ytkit - shared core for the Ultimate YouTube skill.

Every CLI script in ``scripts/`` imports from here so there is exactly one
implementation of authentication, quota tracking, API calls, ID parsing and
output handling.

Modules
-------
config     paths, environment variables, report directory
quota      local tracker for the YouTube Data API daily quota buckets
auth       API key + two separate OAuth tokens (read-only and write)
client     service builders and a safe ``call()`` wrapper (retries, quota, errors)
ids        parse video / channel / playlist IDs, handles and URLs
util       small helpers: durations, dates, numbers, JSON output
analysis   pure, network-free analytics (outliers, cadence, title patterns, comments)
transcript transcript fetching with fallbacks and a local searchable library
"""

__version__ = "1.0.0"
