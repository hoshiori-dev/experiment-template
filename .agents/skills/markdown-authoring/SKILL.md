---
name: markdown-authoring
description: >
  Writes Markdown targeted at a specific rendering engine. Use when markdown
  renders wrong or inconsistently ("the table breaks in mkdocs", "line breaks
  don't show", "math doesn't render"); when authoring for GitHub or GitLab
  READMEs, issues, and wikis, for mkdocs/Docusaurus/Obsidian, or for chat and
  terminal renderers; when adding math, mermaid, footnotes, or admonitions to a
  markdown document; or when converting a document into markdown for a known
  target. Not for the text's prose quality (pair with human-writing), and not for
  LaTeX or Typst sources.
---

# Markdown Authoring

"Markdown" is a family of dialects, not one language. Almost every rendering
problem is a dialect problem: the same file is correct for one engine and
broken in another. Identify the engine first; it decides everything below.

## Identify the rendering engine

Determine the target before writing or fixing anything:

- Repo context: `mkdocs.yml` → mkdocs (Python-Markdown + extensions);
  `docusaurus.config.*` or `.mdx` files → Docusaurus/MDX; a README or issue on
  GitHub → GFM; on GitLab → GLFM; an Obsidian vault → Obsidian.
- Ask, or check where the file will be viewed, when context does not say.
  A file read in chat UIs or terminal viewers is its own (poorest) dialect.
- Multiple targets at once (README rendered on GitHub *and* packaged docs) →
  write to the intersection and flag constructs that will differ.

## Newline and blank-line semantics

The highest-frequency breakage; check it for the specific target:

- **Single newline**: CommonMark, GFM files, mkdocs, and Docusaurus join it
  into a space (soft break). GitHub issues/comments, many chat UIs, and
  Obsidian (by default) render it as a real line break. So: semantic
  linefeeds (breaking source lines at clause boundaries) are safe and
  diff-friendly for soft-break targets, but change visible output on
  hard-break targets — there, one paragraph stays one source line.
- **Hard break on purpose**: a backslash at end of line is the reliable
  CommonMark form; two trailing spaces also work but editors and hooks strip
  them silently. `<br>` where raw HTML is allowed.
- **Blank lines around blocks**: strict engines (Python-Markdown/mkdocs
  especially) require a blank line before lists, headings, and fenced code;
  GFM is forgiving. When output "swallows" a list into the previous
  paragraph, add the blank line.
- **List continuation**: Python-Markdown wants nested content indented 4
  spaces under the item; GFM aligns to the text after the marker. Mixed
  indentation is why nested lists collapse in one engine and not another.

## Out-of-spec constructs

None of these are CommonMark; each needs the engine's own form:

- **Math**: GitHub renders `$...$` / `$$...$$` (beware bare currency `$` in
  the same paragraph); GitLab uses ``$`x`$`` inline and ```` ```math ````
  blocks; mkdocs needs the arithmatex extension plus KaTeX/MathJax assets;
  Docusaurus needs remark-math/rehype-katex. If the engine has no math path,
  fall back to Unicode for simple expressions or pre-rendered images for
  real formulas — do not paste LaTeX and hope.
- **Diagrams**: ```` ```mermaid ```` fences render natively on GitHub and
  GitLab; mkdocs/Docusaurus need plugins; elsewhere ship an image.
- **Footnotes** `[^1]`: GFM, GLFM, and mkdocs (extension) yes; core
  CommonMark and most chat renderers no.
- **Admonitions/callouts** — four incompatible syntaxes: mkdocs `!!! note`,
  Docusaurus `:::note`, GitHub alerts `> [!NOTE]`, Obsidian callouts
  `> [!note]`. Never carry one across engines unconverted.
- **Raw HTML**: GitHub sanitizes (no `<style>`/`<script>`, limited
  attributes); MDX parses HTML as JSX — unclosed `<br>` or `class=` breaks
  the build (`<br />`, `className=`); mkdocs passes HTML through only with
  `md_in_html` for markdown inside it.
- **Emoji shortcodes** (`:tada:`): GitHub/GitLab and some chat apps only;
  literal Unicode emoji are portable.

## Unknown or mixed target

When the engine cannot be determined, write defensive CommonMark and say so:

- ATX headings (`#`) without skipped levels, blank lines around every block,
  fenced code with a language tag, reference-style links for long URLs.
- No math, footnotes, admonitions, or HTML; tables (a GFM extension) are
  near-universal but flag them if the content would be lost without them.
- Hard breaks via backslash; no trailing-space breaks.
