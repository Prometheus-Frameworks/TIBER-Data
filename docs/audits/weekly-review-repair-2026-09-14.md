# Weekly candidate review repair — 2026-09-14

Joe authorized verifying the P1, repairing confirmed findings and obtaining fresh reviews. Task classes: Data artifact and downstream handoff. No source acquisition, admission, merge or deployment.

## P1 verification

GitHub's Git commit API reports that published head `abf06d1d3f5650c5e0fd6f5b6781ca03ddba40c8` has direct parent `a17c2c89f2b7f69fc69691d706290ed882629672`, whose parent is main `93ac73af22da063f37694939a3494bcdf82ae1d4`. Thus the claimed sibling relationship does not describe the published PR graph. The referenced `606c982` is not this PR head.

A fresh single-branch clone from GitHub verifies `git merge-base --is-ancestor a17c2c89f2b7f69fc69691d706290ed882629672 HEAD` and offline `prepare()` using the pinned player/team and schedule support. An initial attempt to clone the local partial repository failed due to missing promisor objects; the fresh remote clone is the relevant reproduction.

No raw pin or history rewrite is warranted for this finding. Future integration must retain support ancestry (merge commit); squash/rebase requires a separately reviewed durable support strategy. A shallow checkout must fetch the pinned ancestry before offline replay. This is not merge authorization.

## Confirmed P2 repair

The initial dated snapshot predated content-key directories. Intake now checks validated existing same-scope snapshot contents before creating a new directory. Exact bytes return the original path and unchanged receipt; corrupt legacy bytes fail closed. No existing raw bytes, receipt clocks, or candidate revision files change.

Changed surfaces: intake script, publication regression tests and this paired audit record. The new real-byte, mocked-network regression fails on the previous implementation and passes after repair. All 29 weekly Data tests pass. Runtime/admission behavior is unchanged.

Audit trigger: fresh independent review pending on the published repair head. No review acceptance, activation, source admission, merge or deployment is implied.
