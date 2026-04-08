# TIBER-Data — Truth Sources and Failure Boundaries

## Canonical truth sources in this repo

Highest authority:
1. versioned contracts under `src/contracts/`
2. deterministic raw/silver/gold data assets committed in the repo
3. export/validation code that is explicitly designed to fail closed
4. README + architecture/governance docs for repo purpose and scope

## What counts as truth

Truth means one of:
- a committed contract
- a committed artifact
- a committed raw support file
- a documented export path that can be reproduced
- a clearly identified upstream source already integrated into the repo

Truth does not mean:
- “the pattern suggests this next week should look similar”
- “the builder can extrapolate the rest”
- “this seems representative”
- “we only need a placeholder for now” unless the placeholder is explicitly marked and approved

## Fail-closed rules

If asked to expand coverage:
- verify the raw support exists
- verify the supported-week intersection honestly expands
- if not, stop at the last supported week

If asked to generate artifacts:
- generate only from committed support inputs
- fail loudly if requested scope exceeds support

If asked to create missing rows:
- do not synthesize them unless the task explicitly creates a synthetic/demo lane
- synthetic/demo lanes must be named as synthetic/demo lanes

## Forbidden moves

- repeating week patterns and calling it season coverage
- silently promoting fixture data into canonical truth
- changing contracts to fit bad data
- inventing provenance after the fact

## Escalation rule

If the repo cannot complete a request honestly, say:
- what exact asset is missing
- what exact scope remains supported
- what repo likely owns the next step
