---
name: typst-authoring
description: >
  Writes and edits Typst source (.typ). Use when a .typ file is the material at
  hand; when typesetting or converting a document, resume, paper, slide deck, or
  report to Typst (including "port this from LaTeX"); when a #set or #show rule,
  template, package import, math block, figure, table, or bibliography misbehaves;
  or when structuring a multi-file Typst project. Includes a syntax primer and
  cheat sheet, since Typst is niche enough that guessing syntax fails. Not for
  LaTeX or Markdown sources, and not for the document's content quality (pair with
  a genre writing skill).
---

# Typst Authoring

Typst is a modern typesetting system with LaTeX's ambitions and a programming
language's coherence. It is niche: guessed syntax is usually LaTeX habits in
disguise, so work from this primer and the docs, not from memory of LaTeX.

## Where to look things up

1. Official docs — https://typst.app/docs/ (language reference and tutorial);
   `typst help` for the CLI.
2. Packages — https://typst.app/universe/ ; every package page documents its
   API. Never guess a package's functions; check its Universe page.
3. The template in use — a `#show: template.with(...)` line means that
   template's own docs and defaults govern the document.

## Syntax primer

Three modes, switched by delimiters:

- **Markup mode** (default): prose plus lightweight markup.
  `= Heading` (level = number of `=`), `- ` unordered item, `+ ` auto-numbered
  item, `/ term: description` term item, `*bold*`, `_emphasis_`, `` `raw` ``,
  ```` ```lang fenced raw blocks ````, `\` forced line break, `// comment`.
- **Code mode**, entered with `#`: `#let x = 3`, `#let f(x) = x * 2`,
  `#set`, `#show`, `#import`, `#include`, and any function call
  (`#figure(...)`, `#table(...)`). Content blocks `[...]` hold markup; code
  blocks `{...}` hold expressions.
- **Math mode**, delimited by `$`: `$x^2$` is inline; spaces inside the
  delimiters (`$ x^2 $`) make it a display block. `_` subscripts, `^`
  superscripts, `frac(a, b)` or `a/b`, symbol names spelled out (`alpha`,
  `arrow.r`, `times`).

Styling flows through two rule kinds:

- `#set` configures an element's defaults from that point on:
  `#set text(font: "Libertinus Serif", size: 11pt, lang: "en")`,
  `#set page(paper: "a4", margin: 2.5cm)`, `#set par(justify: true)`,
  `#set heading(numbering: "1.1")`.
- `#show` transforms elements: `#show heading: set text(navy)` restyles,
  `#show "TODO": strong` rewrites, and `#show: my-template.with(title: [..])`
  wraps the whole remaining document — the standard template mechanism.

Cross-references: attach a label `<intro>` after an element, cite it with
`@intro`; `@key` also cites bibliography entries once a `#bibliography(...)`
exists.

## Project structure

- One entry file (conventionally `main.typ`); compile with
  `typst compile main.typ`, live-preview with `typst watch main.typ`.
- `#include "chapters/one.typ"` splices another file's **content**;
  `#import "lib.typ": helper` (or `: *`) brings in **definitions** without
  rendering anything. Content → include; functions and variables → import.
- Local template pattern: a template file exports a function taking named
  options and the document body; the entry file applies it with
  `#show: template.with(title: [My Title], authors: (..,))`.
- Third-party packages: `#import "@preview/cetz:0.3.1": canvas` — the
  version pin is required. A `typst.toml` manifest is only needed when
  authoring a package, not for using them.

## Source-line discipline

A single newline is only a soft break — a blank line starts a new paragraph.
Target lines of roughly 120 characters, counting CJK characters (汉字, kana) as
two: the length decides when to break, semantics decide where. As a line
approaches the target, break after the sentence-ending punctuation; when one
sentence alone would overrun it, break inside at a comma or another semantic
pause. Consecutive short sentences stay on one line — do not force one
sentence per line, and never break mid-word or mid-phrase at the raw count.
Never add a blank line just to wrap; it changes the output.

## Gotchas

- `#` starts code in markup: literal hashes, dollars, asterisks, and
  underscores need escaping (`\#`, `\$`, `\*`, `\_`).
- `$x$` vs `$ x $` (inline vs display) is decided by the spaces — a diff that
  "only" trims spaces inside `$` changes layout.
- Labels (`<name>`) must directly follow the element they name; a blank line
  in between detaches them.
- Read [references/syntax-reference.md](references/syntax-reference.md) when
  the document needs constructs beyond this primer — figures, tables, math
  details, bibliography setup, page headers/footers, outlines, or common
  `#set`/`#show` recipes.
