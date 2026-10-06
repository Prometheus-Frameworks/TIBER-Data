# TIBER Player EPA Views v0.1
Prepared for Joe on October 5, 2026. Offline prototype for a later TIBER Team integration or data suite.

## Deliverable
Three consistent, inspectable player views. RB and receiving metrics contain source-backed descriptive values; full QB dropback EPA is specified but unavailable. The original offline deliverable made no repository, ROP, Teamstate, Forecast, runtime, deployment or source-admission changes; the Git preservation and verification repair are recorded below.

| View | Numerator | Denominator | Current status |
|---|---|---|---|
| RB EPA per carry | Source rushing_epa | Matching source carries | Populated where both operands are supplied |
| Receiver EPA per target | Source receiving_epa | Matching source targets, including incomplete targets | Populated where both operands are supplied |
| QB EPA per dropback | Chosen play-level EPA across eligible throws, sacks and scrambles | Matching eligible dropbacks with EPA coverage | Unavailable: matching play population and count not supplied |

The source player-week file contains passing_epa, rushing_epa and receiving_epa. Passing EPA includes attempts and sacks and uses qb_epa handling for receiver fumbles; it does not supply the matching full dropback population. Do not relabel passing_epa / attempts or passing_epa / (attempts + sacks) as full EPA/dropback. A later QB definition must explicitly choose epa versus qb_epa and consistently apply it across all eligible events.

## Files
- player-views/*.json: three view datasets with player-game and player-team observed-window grains.
- player_views_builder.py: stdlib-only offline builder, restricted to the exact source digest.
- verify_player_views.py and player-views/check-results.txt: focused checks and results.
- nflverse-current.csv: exact source snapshot.
- original-comparison-provenance.json: prior EPA comparison custody record; includes its own later recording clock.
- package-manifest.json: this package's recording clock, source identity, checks and file digests.

After extracting the archive, run from the extraction directory. The packaged
`player-views/*.json` are frozen goldens: never use that directory as builder
output. Verification checks their recorded digests before comparing a fresh
temporary build. Reproduce with:
```
python verify_player_views.py
reproduction_dir="$(mktemp -d)"
python player_views_builder.py nflverse-current.csv "$reproduction_dir"
python test_golden_boundary.py
rm -r "$reproduction_dir"
```

## Population and interpretation
RB view selects source position RB. Receiving view selects observed RB/WR/TE rows plus any other position with a positive credited target count. QB view selects source position QB. These are source-row position labels, not independently reconstructed cutoff-effective rosters. Display names are labels; joins and aggregation use player_id and event team. Team changes remain separate groups.

Window = available 2026 REG rows in requested W1–W4, not four assumed player games. The snapshot represents 16 games in each of W1–W3 and 15 in W4; ATL–NO is absent. An absent player row does not establish zero, DNP, a bye or a missed game. Do not fill missing weeks. All outputs carry requested_weeks, observed_weeks and game_ids. The observed window is not proof of a complete player-season population.

Aggregate unrounded EPA sums and matching counts, then divide once; never average weekly rates without weights. Negative EPA is valid. Missing operands block a complete aggregate, even if another row is available. Zero opportunities have no rate. No league-average fills, invented dropbacks, opportunity thresholds, rank claims or predictive interpretations. A small sample can produce an extreme rate; always display its count.

These are source-aggregate ratios. They do not apply custom PBP exclusions for penalties, kneels, laterals or two-point plays. A future custom-filtered metric needs a separately versioned definition and compatible operands.

EPA describes the scoring value of plays involving a player; it does not isolate the player's causal contribution from blocking, quarterback, opponent or game situation. Receiving EPA includes unsuccessful targets. These views complement role and opportunity observations rather than replace them.

## Suggested TIBER Team presentation
One reusable card per view:
- Player, team, metric and source/model label.
- EPA per opportunity beside total EPA and opportunity count.
- Weekly history, with missing weeks explicitly unavailable.
- Requested window, observed games and partial-week badge.
- Inspectable operands, source revision and release clock.
- For QB: visible unavailable state and exact dependency, with supplied passing stats shown only as context.

No default starter recommendation or ranking. A later comparison should use compatible windows, definitions and explicit sample rules. Pair RB carry efficiency with receiving usage; pair receiver target efficiency with target allocation. Keep ROP role statements and efficiency observations distinguishable.

## Evidence and authority
Pinned source: https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_2026.csv
Asset: 612530012. Release update: 2026-10-05T12:33:41Z.
SHA-256: 27a8a464687901340e87873010b3583443619fad723db828f745f71c8086ec9e
Size: 1,950,079 bytes. Exact bytes matched release metadata in the earlier comparison.
W1–W3 retained rushing EPA matched the later source by player-game identity. This is descriptive later-revision evidence, not proof of historical pre-cutoff availability. Original retrieval clock was not separately witnessed; do not substitute the package recording clock.

Official definitions: https://nflfastr.com/reference/nfl_stats_variables.html
Attribution: nflverse contributors. CC BY 4.0 per the retained dataset receipt: https://creativecommons.org/licenses/by/4.0/ . No endorsement implied.

This user-authorized package is for offline examination and future design. It creates no general source acceptance, no retrospective approval receipt and no current production pointer. The original package claimed no independent review; the later archival audit is recorded in the Git publication handoff below. The supplied NGS quotation is not a calibration target or canonical truth for these views.

## Smallest future integration
Data owns operand and source qualification. ROP remains the observed role layer. TIBER Team may later assemble these observations in a consumer card after contract reconciliation and independent review. Reconcile existing work before adding any issue or implementation lane. The next integration proposal should name exact files, selected recipients/positions, missingness semantics, tests, source-purpose receipt and UI acceptance scope. Full QB EPA/dropback needs separately qualified retained PBP; no new acquisition occurred while packaging this snapshot.


## Git publication handoff

Active task: preserve the already-created offline package in Git, under Joe's October 5 publication request.

Task classification: data-artifact archival publication and downstream handoff documentation. No new derivation or source acquisition in this publication step.

Files touched: this README, TIBER-Player-EPA-Views-v0.1.zip and SHA256SUMS, plus the paired independent audit records under `docs/audits/`. The archive contains the original spec, builder, focused checks/results, exact source CSV, three JSON views and package manifest. The original archive was committed at `128a45feec7782bb57d6b4dc563409e0197549ca`; this repair changes only reproduction docs, verification/test code, check results and manifest. Source CSV, original provenance and all three JSON goldens remain byte-for-byte unchanged.

Now true: the complete offline package is committed to this unmerged publication branch. Raw numerical values are inspectable through the archive. The builder and synthetic/frozen-source checks previously passed; archive integrity and member digests were verified. This publication does not convert the archived script into an operational producer.

Still missing: final exact-head PR review, operator merge decision, general source-purpose admission, QB full-dropback evidence/definition qualification, complete Week 4 coverage and finality, and any consumer integration acceptance.

Must not be assumed: publication is not merge approval, promoted truth, current NFL coverage, a production contract, UI activation or an authorization to expand producer work. The snapshot is frozen and remains partial W4 even after later games become available.

Audit-trigger status: **independent audit completed — clean with nonblocking notes, archival only**. Provenance, support wording, generated observations and handoff semantics trigger Data's auditor requirement. See [human-readable audit](../../audits/player-epa-views-v0.1-2026-10-05.md) and [machine-readable disposition](../../audits/player-epa-views-v0.1-2026-10-05.json). The auditor independently reconciled the frozen population and checked the repaired archive and README; this is not source admission, consumer acceptance or merge approval. Final exact-head PR review is recorded separately in the PR discussion.

Archive SHA-256: 4410b0bb78ddd589099654c3869c0b941c1b024caf7262e65f91bf602afa1990 (416,857 bytes).
Original archive SHA-256: a1bd69ce45848339101594a705b5a034b4e67249521a1ad9ac509e2a03d179b2 (415,146 bytes); recoverable at the original commit.

Relationship to existing work: Data #273 governs weekly candidate publication; #277/#278 retain the W3 source/replay lane. This archive does not replace their receipts or authorize their consumers. Research #28's team rushing-environment design remains separate from these individual source-aggregate views. Existing target/receiving opportunity work remains under its existing owner; no new implementation lane is assigned here.
