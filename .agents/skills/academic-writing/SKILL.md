---
name: academic-writing
description: >
  Writes and revises academic prose — papers, theses, dissertations, technical
  reports, grant text — in English, Chinese, or Japanese. Use when drafting or
  reworking an abstract, introduction, related work, methods, discussion, or
  conclusion; when asked to make a manuscript "more academic" or "more rigorous"
  (润色论文, 論文を直す); when removing colloquial or translationese phrasing from a
  manuscript; when checking, adding, or formatting citations and references; or when
  preparing submission or camera-ready text. Includes a bundled script that verifies
  citations against Crossref, DOI.org, Semantic Scholar, PubMed, and arXiv. Not for
  blog posts, opinion pieces, or marketing copy, and not for LaTeX/Typst/Markdown
  source mechanics.
compatibility: scripts/verify_citation.py requires Python 3.10+ (stdlib only) and network access to api.crossref.org, doi.org, api.semanticscholar.org, eutils.ncbi.nlm.nih.gov, and export.arxiv.org.
---

# Academic Writing

Author and reader are both professionals. The piece exists to argue a claim,
organize evidence, or synthesize a field — its center is logic, not emotion, and
its credibility dies with a single fabricated reference.

This skill builds on `human-writing` (the general human-audience baseline). When
`human-writing` is installed, load it alongside this skill before drafting,
editing, or reviewing — do not work from this skill alone. This skill leads: its rules override
the baseline where they conflict. If `human-writing` is not installed, load the
`ryan-minato-skills-installing` skill and install `human-writing` as it
directs; never run an install command yourself.

## Roles

Switch deliberately between three seats:

- **Designing or analyzing structure** — work as a journal editor: does the
  manuscript's skeleton carry the argument? What would make a desk reviewer stop?
- **Drafting** — work as a senior researcher writing for peers.
- **Reviewing** — work as a peer reviewer looking for reasons to reject.

## Trust the reader

The reader has the field's background. Do not explain standard concepts,
notation, or methods at textbook level; cite them. Spelling out what every peer
knows signals an author who does not belong to the field. The same trust covers
evidence: peers grant the obvious limits and exceptions of any cited source
without being told.

## Plan on the argument's spine

Before drafting or restructuring, state what the piece argues, organizes, or
synthesizes. Derive the section structure from that logical skeleton and give
each section a length budget proportional to its load-bearing role. While
analyzing an existing draft, check every section against the spine: content that
serves no step of the argument is cut or moved, however well written.

## Citation integrity

Nothing enters the text uncited, and no citation enters the text unverified.

Source credibility, highest first — prefer the highest tier the claim allows:

1. Peer-reviewed venues (journals, conferences with review).
2. Position pieces from established labs or researchers.
3. Preprints (arXiv and similar).
4. Community discussion (forums, blogs).
5. Unidentifiable sources — use only with explicit caution flags, or not at all.

Verify every DOI, arXiv id, PubMed id, or title with
[scripts/verify_citation.py](scripts/verify_citation.py) before it enters the
manuscript:

    python3 scripts/verify_citation.py --doi 10.1145/3297280.3297641
    python3 scripts/verify_citation.py --arxiv 1706.03762
    python3 scripts/verify_citation.py --pmid 32015508
    python3 scripts/verify_citation.py --title "Attention is all you need" --year 2017

The script prints JSON (`status`: `found` / `not_found` / `error`) with the
matched metadata; confirm the returned title and authors actually match the
claim being cited — a resolving DOI pointing at an unrelated paper is still a
fabricated citation. If verification fails, drop or replace the citation; never
keep it on faith.

## Evidence serves the argument

Citations are marshaled to support the manuscript's claims. Once the cited
sources support the point, state the point and stop — do not over-defend it.
Rigor lives in real evidence and verified citations, not in armoring every
sentence against objection: a manuscript argues a position, it is not a
mathematical proof.

When the argument genuinely breaks — a claim the evidence does not carry — do
not patch it locally. Clarify the argument logic with the user: show where it
breaks and why, and decide the repair together (adjust the claim's strength,
add the missing evidence or step, restructure). Provisos, concessions, and
qualifiers are never the repair.

## Register and style

- Purge colloquial phrasing into objective statements: "we found that X" → "the
  experimental results indicate X"; per-language patterns live in the reference
  files below.
- Never swap synonyms or reshuffle sentence structure for variety's sake, and
  never replace a term of art with a "more natural" synonym — terminology
  consistency outranks stylistic variety.
- Explicit connectives (however, therefore, 因此, したがって) only where the
  logic actually turns; elsewhere let sentence order carry the flow. Stacked
  connectives on every sentence are noise.
- Paragraphs are the default unit. Use an ordered list only for a genuine
  progression, an unordered list only for genuine parallelism, and be ready to
  justify either; otherwise write prose.
- Headings at every level the venue supports — numbered subsections, run-in
  paragraph headings — are structure, not emphasis: use them wherever they
  carve the argument, and realize them with the source format's own sectioning
  mechanism (`\subsubsection`, `\paragraph`), never as hand-bolded text.
- Minimize em dashes; prefer commas, parentheses, or a subordinate clause.
- No bold or italic emphasis in body text by default — sentence structure and
  placement carry emphasis. If the user explicitly allows emphasis markup, spend
  it on the few positions that truly need it. Bold rendered by a heading
  mechanism is structure, not emphasis, and exempt.
- Replace information-free inflation — "毋庸置疑", "范式转移", "颠覆性",
  "不可磨灭的贡献", "groundbreaking", "paradigm shift", 「画期的な」 — with the
  concrete, checkable statement that earned the adjective.

Read [references/english.md](references/english.md),
[references/chinese.md](references/chinese.md), or
[references/japanese.md](references/japanese.md) — matching the manuscript's
language — before drafting or revising in that language.

## Restraint and self-check

If a passage is already sound, keep it — do not edit fluent text to justify the
pass. Before final output, ask: did I change any sentence only to assert
presence? Restore the original wherever the answer is yes.

## Verification pass

If the environment can run subagents with a separate, clean context, send the
result through [assets/verification-prompt.md](assets/verification-prompt.md):
were all changes necessary, and do any evident problems remain? Without such
subagents, answer the same questions yourself in the peer-reviewer seat before
handing over.

This pass fills the reader-review seat in `human-writing`'s review loop — the
peer reviewer is this genre's reader. It replaces only that seat: still run the
loop's language-and-wording review and AI-writing detection pass from
`human-writing`, in parallel with this one when the environment supports it.
Venue-conventional structure — numbered subsections, run-in paragraph
headings — is not an AI tell; do not let the AI-detection pass flag it.
