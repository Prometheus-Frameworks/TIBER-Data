# rb_contact_evasion_observations_v0 fixture corpus

Contract fixtures for TIBER-Data #234, Slice A. See
`docs/contracts/rb-contact-evasion-observations-v0.md` for the full contract.

**Every value in this directory is synthetic.** No fixture contains acquired
provider data, and no external source was accessed to produce any of it. Source
owners are `example_*` placeholders; snapshot ids are marked synthetic; every
observation declares its synthetic nature in `warnings`.

- `positive/` — P1–P7. Each must validate through the public contract gate.
- `negative/` — N1–N15. Each is deliberately **shape-valid** and must be rejected
  by exactly one reason code, so the rejection is attributable to the contract
  rule it exercises rather than to a parse failure.

Fixtures other than the Bucky golden trace use the reserved synthetic canonical
identity `00-0000001`, which corresponds to no real player.

`p7_bucky_receipt_remains_partial.json` uses governed canonical identity
`00-0039361` as the golden-trace identity authorized by #234. Its values are
synthetic and are **not** evidence about Bucky Irving or any real player.
