# WorkProof — test cases

Run manually in GenLayer Studio after deploying
`contracts/work_proof.py` (no constructor args).

## Deterministic validation

1. `submit_work` with a title shorter than 5 characters —
   expect rejection ("title too short").
2. `submit_work` with a non-https PR URL — expect rejection
   ("PR URL must be https").
3. `submit_work` with a GitHub URL that is not a pull request
   (for example `https://github.com/hotwired/hotwire-rails`) —
   expect rejection ("PR URL must be a github.com pull request
   URL").
4. `submit_work` with criteria shorter than 10 characters —
   expect rejection ("criteria too short").
5. `submit_work("Fix typo in README", "https://github.com/hotwired/hotwire-rails/pull/39.patch", "Fixes a typo in the README file")` — expect
   work id `0`, and `get_work_count()` returns `1`. Use the
   `.patch` URL: the PR web page renders almost no diff text,
   while the `.patch` URL shows the actual changes.
6. `get_status(99)` on unknown work — expect rejection
   ("unknown work").
7. `resolve_work(99)` on unknown work — expect rejection
   ("unknown work").

## Non-deterministic verdict paths

8. Resolve the hotwire-rails PR #39 work from case 5 — the PR
   is merged and titled "Fix typo in readme". Expect
   `VERIFIED`, with a reason naming the typo fix, and
   `is_verified(0)` returns `true`.
9. Submit the same PR #39 again with criteria it does not meet
   — criteria `Adds a dark mode toggle to the settings page` —
   and resolve it. The PR only fixes a typo ("complimentary" to
   "complementary" in README.md), so expect `NOT_VERIFIED`.
10. Submit a pull request URL that does not exist — for
    example `https://github.com/hotwired/hotwire-rails/pull/999999.patch`
    with criteria `Fixes a typo in the README file` — and
    resolve it. The page carries no usable evidence, so expect
    `INCONCLUSIVE`. (Also: resolve an already-resolved work a
    second time — expect rejection ("work already resolved"). A
    VERIFIED item that is later reverted stays VERIFIED in its
    own record; submit new work for a fresh check.)
