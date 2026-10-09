---
name: latex-authoring
description: >
  Writes, edits, and reflows LaTeX source. Use when a .tex file is the material at
  hand; when converting a draft into LaTeX or into a journal or conference class
  (acmart, IEEEtran, llncs, article); when fixing LaTeX compile errors, package
  usage, or environment syntax; when typesetting math, figures, tables, or
  bibliographies in LaTeX; or when reformatting LaTeX source lines for clean diffs.
  Not for the document's content or prose quality (pair with a genre writing
  skill), and not for Typst or Markdown sources.
---

# LaTeX Authoring

LaTeX source is code that compiles into a document: edit it with a programmer's
discipline (look up APIs, keep diffs clean) while the compiled output stays a
typesetting concern.

## Look it up, don't guess

Resolution order when syntax or behavior is uncertain:

1. **The document's own class and template docs** — journal and conference
   classes (acmart, IEEEtran, llncs) override standard behavior and forbid
   packages; their guides and sample files are the law for that document.
2. **Package documentation** — `texdoc <package>` locally, or the package's
   CTAN page (https://ctan.org/pkg/<package>) for the same PDF.
3. **General syntax** — Overleaf Learn (https://www.overleaf.com/learn) for
   environments, math, and common recipes.

Niche macro syntax guessed from memory is the main source of broken builds;
check the docs for anything beyond everyday commands.

## Source-line discipline

LaTeX ignores a single newline: only a blank line starts a new paragraph. So
long source lines are broken with plain newlines without changing the output —
and must be.

- Target lines of roughly 120 characters, counting CJK characters (汉字, kana)
  as two. The length decides *when* to break; semantics decide *where*: as a
  line approaches the target, break at the end of the current sentence, and
  when a single sentence alone would overrun it, break inside at a comma or
  another semantic pause. Consecutive short sentences stay on one line — do
  not force one sentence per line. Never break mid-word or mid-phrase at the
  raw count. Semantic breaks keep `git diff` aligned with meaning: editing
  one sentence touches one line or a few adjacent ones.
- Never insert a blank line just to wrap — a blank line is a paragraph break.
  Inside math and other display environments a blank line is an error.
- To break a line where a newline would insert an unwanted space (inside macro
  arguments, after an opening brace), end the line with `%`: the comment
  character eats the newline.

## Gotchas

- A control word eats the space after it: `\LaTeX is` typesets as "LaTeXis".
  Write `\LaTeX{} is` (or `\LaTeX\ `).
- Quotes are `` ` `` / `'` and ``` `` ``` / `''`, not the `"` character.
- Dashes: `-` hyphen, `--` number ranges, `---` punctuation dash; a minus sign
  only inside math mode.
- Tie references with a non-breaking space: `Figure~\ref{fig:x}`,
  `Section~\ref{sec:y}`, `\cite` preceded by `~` where a line break would
  strand the bracket.
- `\label` goes after (or inside) `\caption`, never before it, or the number
  is wrong.
- Escape reserved characters in text: `% $ & # _ { }` (as `\%` etc.); `\\` is
  a line break, `\backslash`/`\textbackslash` is the character.
- Load `hyperref` near the end of the preamble (cleveref after it); many
  package conflicts are ordering problems.
- `\input{file}` splices source (no page break implications); `\include`
  forces a page break and supports `\includeonly` — pick by document size.
