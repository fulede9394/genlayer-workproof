# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import typing


class WorkProof(gl.Contract):
    """
    WorkProof - did this pull request actually do the stated work?

    Bounties, grants and freelance jobs all end in the same
    argument: the work was submitted, but was it actually done?
    A merged pull request is not proof by itself - it may fix
    something else entirely, or change nothing that matters.
    Someone has to read the diff and check it against what was
    promised, and that check is subjective: it needs judgment,
    not a string comparison.

    This contract turns "the work is done" into a checkable
    on-chain record. The submitter fixes two things at
    submission time: the pull request URL and the acceptance
    criteria the work was supposed to meet. Validators then read
    the pull request and judge it against those criteria.

    Consensus follows the judgment pattern, not the extraction
    pattern. The LLM does not extract a field for code to
    compare; it judges, and returns one line:

      VERDICT|REASON

    VERDICT is VERIFIED, NOT_VERIFIED or INCONCLUSIVE, and
    REASON is one short sentence. The line is judged under
    prompt_non_comparative: two judgments are equivalent when
    they reach the same verdict word, whatever the reason says.
    Deterministic code then only parses the verdict word and
    stores the reason for the audit trail - it never second-
    guesses the judgment.

    That is the whole point, and what makes this contract a
    different shape from a status oracle: the verdict is a
    judgment against submitter-defined criteria, the evidence
    is a code diff rather than a status page, and there is no
    field for deterministic code to compare. A pull request
    that does something else is NOT_VERIFIED, not MISMATCH;
    a page that cannot be read is INCONCLUSIVE, not UNKNOWN.
    """

    work_count: u256
    work_titles: TreeMap[u256, str]
    pr_urls: TreeMap[u256, str]
    criteria_texts: TreeMap[u256, str]
    statuses: TreeMap[u256, str]
    reasons: TreeMap[u256, str]

    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    NOT_VERIFIED = "NOT_VERIFIED"
    INCONCLUSIVE = "INCONCLUSIVE"

    def __init__(self):
        self.work_count = u256(0)

    def _is_pr_url(self, url: str) -> bool:
        # A pull request URL must be a GitHub pull URL.
        if "github.com" not in url:
            return False
        if "/pull/" not in url:
            return False
        return True

    @gl.public.write
    def submit_work(
        self,
        title: str,
        pr_url: str,
        criteria: str,
    ) -> int:
        title = title.strip()
        pr_url = pr_url.strip()
        criteria = criteria.strip()

        assert len(title) >= 5, "title too short"
        assert len(title) <= 200, "title too long"
        assert pr_url.startswith("https://"), "PR URL must be https"
        assert len(pr_url) <= 300, "PR URL too long"
        assert self._is_pr_url(pr_url), "PR URL must be a github.com pull request URL"
        assert len(criteria) >= 10, "criteria too short"
        assert len(criteria) <= 1000, "criteria too long"

        wid = self.work_count
        self.work_titles[wid] = title
        self.pr_urls[wid] = pr_url
        self.criteria_texts[wid] = criteria
        self.statuses[wid] = self.PENDING
        self.reasons[wid] = ""
        self.work_count = wid + u256(1)
        return int(wid)

    @gl.public.write
    def resolve_work(self, work_id: int) -> str:
        wid = u256(work_id)
        assert wid in self.statuses, "unknown work"
        assert self.statuses[wid] == self.PENDING, "work already resolved"

        # Copy storage into locals: non-deterministic blocks may not
        # touch contract storage, they may only capture local values.
        title = self.work_titles[wid]
        pr_url = self.pr_urls[wid]
        criteria = self.criteria_texts[wid]

        def judge_work() -> str:
            page = gl.nondet.web.render(pr_url, mode="text")
            prompt = f"""Judge whether a GitHub pull request satisfies the stated acceptance criteria, using only the pull request content below. Use the pull request's .patch URL, which shows the actual diff, so the changes are visible.

Work: {title}
Acceptance criteria: {criteria}

Pull request content:
{page[:4000]}

Reply with exactly one line, nothing else, in this format:
VERDICT|REASON

VERDICT is one of:
VERIFIED - the pull request's changes satisfy all of the acceptance criteria
NOT_VERIFIED - the pull request's changes do not satisfy the criteria, or the pull request is about something else entirely
INCONCLUSIVE - the page could not be read, or it carries too little evidence to judge either way

REASON is one short sentence explaining the verdict. Judge the changes shown on the page, not the pull request's title alone."""
            return gl.nondet.exec_prompt(prompt).strip()

        line = gl.eq_principle.prompt_non_comparative(
            judge_work,
            principle="Two judgments are equivalent when they give the same verdict word: VERIFIED, NOT_VERIFIED, or INCONCLUSIVE. The reason text does not matter.",
        )

        # Deterministic parsing only: the verdict word is taken
        # from the agreed line, the reason is stored for audit.
        first_sep = line.find("|")
        if first_sep == -1:
            verdict_word = line.strip().upper()
            reason = ""
        else:
            verdict_word = line[:first_sep].strip().upper()
            rest = line[first_sep + 1:]
            reason = rest.strip()
        self.reasons[wid] = reason

        if verdict_word == "VERIFIED":
            final = self.VERIFIED
        elif verdict_word == "NOT_VERIFIED":
            final = self.NOT_VERIFIED
        else:
            final = self.INCONCLUSIVE

        self.statuses[wid] = final
        return final

    @gl.public.view
    def get_work(self, work_id: int) -> typing.Any:
        wid = u256(work_id)
        assert wid in self.statuses, "unknown work"
        return {
            "id": work_id,
            "title": self.work_titles[wid],
            "pr_url": self.pr_urls[wid],
            "criteria": self.criteria_texts[wid],
            "status": self.statuses[wid],
            "reason": self.reasons[wid],
        }

    @gl.public.view
    def get_status(self, work_id: int) -> str:
        wid = u256(work_id)
        assert wid in self.statuses, "unknown work"
        return self.statuses[wid]

    @gl.public.view
    def is_verified(self, work_id: int) -> bool:
        wid = u256(work_id)
        assert wid in self.statuses, "unknown work"
        return self.statuses[wid] == self.VERIFIED

    @gl.public.view
    def get_work_count(self) -> int:
        return int(self.work_count)
