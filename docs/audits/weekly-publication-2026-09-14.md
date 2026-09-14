# Published branch preparation — 2026-09-14

Joe authorized pushing both branches and opening paired draft PRs to test whether PR preview deployments are disabled. Keep drafts for Joe to mark ready; no merge, data admission or manual deployment authorized.

Git CLI has no write credentials. Publication uses the authenticated GitHub connector, producing new commit IDs. All raw source bytes were checked against their original Git blob IDs and published first at `a17c2c89f2b7f69fc69691d706290ed882629672`.

The new latest candidate is `5f86ec5d56d2965d17ac58e860f9f107c648d3d367adbf2c7a73c4f316dbc0db`, under the same `exports/candidates/weekly_boxscore/revisions/2026_REG_w01` stream. It references that published commit for player/team and schedule support. The published-support replay is `weekly-boxscore-replay-2025-published-v0.json`: 18 weeks, 272 games, same observations and reconciliation as the local replay.

Earlier candidate revisions and audit reports remain unchanged as records of local preparation. Their old local-only commit IDs are not promised as fetchable GitHub objects. For new replay use the published support commit above; all corresponding raw file paths and bytes are identical. No original acquisition timestamps were rewritten. Changed artifact hashes result from published support references, not changes to player facts or scoring policy. Runtime remains unadmitted.
