# Typst cheat sheet

Load when the document needs constructs beyond the SKILL.md primer. When a
detail here conflicts with https://typst.app/docs/ for the installed Typst
version, the docs win — check them for anything version-sensitive.

## Figures and images

```typst
#figure(
  image("plots/speedup.png", width: 80%),
  caption: [Speedup over baseline.],
) <fig-speedup>

As @fig-speedup shows, ...
```

`image` accepts `width`/`height` (lengths or `%`), `fit`. `#figure` also wraps
tables and code listings; set `kind: table` or `kind: raw` to group numbering.

## Tables

```typst
#table(
  columns: (auto, 1fr, 1fr),      // count or per-column widths
  align: (left, center, center),
  table.header([Name], [Metric], [Value]),
  [baseline], [latency], [8.0 s],
  [ours],     [latency], [1.2 s],
)
```

Cells are content blocks in row-major order. `table.cell(colspan: 2)[..]`
spans; `stroke: none` removes rules; `#grid(...)` is the layout twin without
table semantics.

## Bibliography and citations

```typst
#bibliography("refs.bib", style: "ieee")   // .bib or Hayagriva .yml
```

Cite with `@key` (or `@key[p. 7]` for a supplement); `#cite(<key>, form:
"prose")` for textual forms. The bibliography renders where the call sits.

## Math details

- Inline `$x$`; display `$ x $` (spaces inside the delimiters decide).
- `x_1`, `x^2`, `x_(i+1)`; `frac(a, b)` or `a/b`; `sqrt(x)`, `root(3, x)`.
- Multi-letter identifiers are upright text; single letters are variables —
  write `"loss"` (quoted) for words, `op("argmax")` for operators.
- Symbols by name: `alpha`, `beta`, `infinity`, `arrow.r`, `times`, `dot`,
  `lt.eq`, `approx`; `vec(1, 2)` vectors, `mat(1, 2; 3, 4)` matrices,
  `cases(x &"if" x > 0, 0 &"otherwise")`.
- Align display math with `&`; number equations via
  `#set math.equation(numbering: "(1)")`, then label and `@ref` them.

## Page setup and front matter

```typst
#set page(
  paper: "a4",
  margin: (x: 2.5cm, y: 2cm),
  header: align(right)[Draft — #datetime.today().display()],
  numbering: "1 / 1",
)
#set text(font: "Libertinus Serif", size: 11pt, lang: "zh")  // lang drives
#set par(justify: true, leading: 0.8em)                      // hyphenation/CJK
#set heading(numbering: "1.1")
#outline(depth: 2)          // table of contents
#pagebreak()
```

`lang` matters for CJK: it selects line-breaking and quotation behavior; pair
it with a CJK font via `#set text(font: ("Libertinus Serif", "Noto Serif CJK SC"))`
(fallback list).

## Common show-rule recipes

```typst
#show heading.where(level: 1): set text(1.2em)
#show heading: it => { v(0.5em); it }        // space above headings
#show link: underline
#show raw.where(block: true): block.with(fill: luma(245), inset: 8pt,
  radius: 4pt)
#show "FIXME": text.with(red)
```

## Layout odds and ends

- `#align(center)[...]`, `#h(1fr)` horizontal filler, `#v(1em)` vertical
  space, `#box(...)` inline container, `#block(...)` breakable container.
- `#columns(2)[...]` multi-column flow; `#place(top + right)[...]` absolute
  placement.
- `#footnote[...]` footnotes; `#quote(attribution: [...])[...]` block quotes.
- Lengths: `pt`, `mm`, `cm`, `em`, `%`, and `fr` (fractional shares);
  colors: `rgb("#1f6feb")`, `luma(240)`, named (`navy`, `red`).
- Raw blocks highlight by language tag: ```` ```rust ... ``` ````; inline raw
  with `` `code` ``.

## CLI

- `typst compile main.typ [out.pdf]`; `typst watch main.typ` live rebuild.
- `typst init @preview/<template>` scaffolds from a Universe template.
- `--root <dir>` when files reference paths above the entry file's folder;
  `--font-path <dir>` for project-local fonts.
