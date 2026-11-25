# WorkProof — Pull Request Work Verification Primitive

A standalone Intelligent Contract that attests whether a GitHub
pull request actually did the stated work, instead of trusting
that a merged PR is a finished job.

## Deployed

- Network: StudioNet (GenLayer Studio)
- Contract: TBD
- Deploy tx: TBD
- Explorer: TBD
- Studio: TBD

## Why this exists

Bounties, grants and freelance jobs all end in the same
argument: the work was submitted, but was it actually done? A
merged pull request is not proof by itself — it may fix
something else entirely, or change nothing that matters.
Someone has to read the diff and check it against what was
promised, and that check is subjective: it needs judgment,
not a string comparison. WorkProof turns "the work is done"
into a reusable primitive with a visible audit trail.

1. `submit_work(title, pr_url, criteria)` — the work, the pull
   request URL and the acceptance criteria are fixed at
   submission time.
2. `resolve_work(work_id)` — validators read the pull request
   and judge it against the criteria. The LLM judges; it does
   not extract a field for code to compare.
3. The verdict is `VERIFIED`, `NOT_VERIFIED` or `INCONCLUSIVE`,
   with a one-sentence reason stored on-chain for audit.

## Judgment, not extraction

The LLM returns one line, `VERDICT|REASON`, judged under
prompt_non_comparative: two judgments are equivalent when
they reach the same verdict word, whatever the reason says.
Deterministic code then only parses the verdict word — it
never second-guesses the judgment. A pull request that does
something else is `NOT_VERIFIED`, not a mismatch; a page
that cannot be read is `INCONCLUSIVE`, not unknown.

## State design

One-way state machine per work item:
`PENDING -> VERIFIED | NOT_VERIFIED | INCONCLUSIVE`

- `VERIFIED`: the pull request's changes satisfy all of the
  acceptance criteria.
- `NOT_VERIFIED`: the changes do not satisfy the criteria, or
  the pull request is about something else entirely.
- `INCONCLUSIVE`: the page could not be read, or it carries
  too little evidence to judge either way.

Because the reason is stored, anyone can see *why* the
verdict came out that way, instead of getting a single
opaque word.

## Try it in GenLayer Studio

1. Paste `contracts/work_proof.py` into Studio and deploy (no args).
2. `submit_work` with, for example:
   - title: `Fix typo in README`
   - pr_url: `https://github.com/hotwired/hotwire-rails/pull/39.patch`
   - criteria: `Fixes a typo in the README file`
3. `resolve_work(0)`, then `get_work(0)` — expect `VERIFIED`
   with a reason naming the typo fix.

Use the pull request's `.patch` URL, not the PR web page: the
web page renders almost no diff text, while the `.patch` URL
shows the actual changes for validators to judge.

## Tests

See `tests/test_cases.md` (10 cases): input validation, unknown /
double resolution, and all three terminal states.
