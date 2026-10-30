---
name: formatacao
description: Use whenever you change the layout, build options or LaTeX setup of the dissertation (report/main.tex, report/Makefile, the class, page breaks, spacing, floats), before any PR that touches report/, before a release, or when the user asks about formatting ("formatação", "margens", "páginas em branco", "número de página", "cabeçalho", "quebras", "frente e verso", "versão digital/impressão").
---

# formatacao

The dissertation must keep the formatting of the official template
(MEI-ISEP/tmdei-dissertation-template). The template guide
(`report/reference/tmdei-template-guide.pdf`, §1.3 and §2.7.1) says:
«Please follow the margins and fonts defined in this template. The font size
should be 11pt. The document should be printed double sided.»

Formatting is "document structure / consistency" in the PREPD grading grid,
so drifting from the template costs marks. Your job is to keep it identical,
not to improve it.

`FC` below means `.agents/skills/formatacao/scripts/fmt-check`, run from the
repo root (not on `PATH`). It needs `pdfinfo`, `pdftotext` and `pdffonts`
(poppler-utils). With `--sem-pdf` it runs only the template and log checks.

## What the template looks like (do not "fix" these)

| Aspect | Template behaviour | Why |
|---|---|---|
| Paper, font | A4, 11 pt, single spacing, paragraph spacing (`parskip`) | guide §1.3 |
| Margins | inner 3.5 cm, outer 2.6 cm, top 3.5 cm, bottom 2.5 cm | `tmdei-style.cls` geometry |
| Two-sided | inner/outer swap on odd/even pages | «printed double sided» |
| Page number | top of the page, **outer** corner of the header (right on odd pages, left on even pages, including chapter openings); none on the title page and on the blank pages before a chapter | guide §2.7.1 |
| Running header | chapter (even pages) / section (odd pages) on the inner side | guide §2.7.1 |
| Blank pages | every chapter and front-matter list (Resumo, Abstract, Índice, Listas) starts on an **odd** page, so a blank even page is inserted when needed; short chapters therefore add blank pages | `openright` |
| Front matter | roman page numbers; main text restarts at 1 | template |
| Lists | only lists with entries: comment `\listoffigures`, `\listoftables`, … while there is nothing to list (`EMPTY-LIST`) | guide §2.6 |

## Build variants

The variants are passed to LaTeX by the `Makefile`, before `main.tex`. Never
edit the class options for them.

| Variable | Values | Effect |
|---|---|---|
| `VERSAO` | `rascunho` (default) · `final` | `final` hides the red «Por fazer» `\todo{}` boxes |
| `FORMATO` | `impressao` (default) · `digital` | `digital` = one-sided: no blank pages, no alternating margins, for screen reading |
| `LINHA` | `0` (default) · `1` | `1` draws the rule under the header (off by default, as template fc0b8f9 compiles) |

```sh
cd report
make docker                                  # main.pdf (draft, print)
make docker VERSAO=final FORMATO=digital     # main-final-digital.pdf
make docker-ambos / make docker-ambos-final  # print + digital (what CI releases)
```

Output: `main$(SUFIXO).pdf` and `build$(SUFIXO)/` (e.g. `main-digital.pdf`,
`build-digital/`).

- Releases carry both PDFs: `…-impressao.pdf`, the official two-sided version,
  and `…-digital.pdf`.
- **Submit the print version** (the guide requires two-sided) unless the
  advisor says otherwise.

## Procedure

1. Build both formats of the version you are working on (`make docker-ambos`,
   or `docker-ambos-final`).
2. Run `FC` on each:

   ```sh
   .agents/skills/formatacao/scripts/fmt-check                                   # print
   .agents/skills/formatacao/scripts/fmt-check --pdf report/main-digital.pdf --build report/build-digital
   ```

   For final: `--pdf report/main-final.pdf --build report/build-final`, and the
   same with `-final-digital`.

   Exit codes: `0` clean; `3` warnings to decide; `1` errors; `2` bad input
   (missing build, PDF or poppler).
3. Fix every error. Decide every warning (below). Never silence one without a
   reason.
4. Look at the pages you touched (`pdftoppm -f N -l N -r 60 -png …`): a check
   is not a substitute for looking.
5. Review with `sol-loop` and then `council` (`AGENTS.md`, «Skills»). Review
   focus: the template is unchanged (class, options, layout), and the pages
   you touched look right in both PDFs.
6. Report: what you changed, the `FC` result for each format, the remaining
   info lines with their reason, and the review outcome.

## Rules

**Never change** (`TEMPLATE-CHANGED`, `CLASS-OPTION`, `LAYOUT-CMD` errors):

- `report/tmdei-style.cls` and `report/.latexmkrc` (checked by hash against
  `referencia-modelo.txt`);
- the `\documentclass` options other than the language: no `oneside`,
  `openany`, `12pt`, `onehalfspacing`, `draft` or `headsepline` in `main.tex`
  (use the build variants);
- margins, paper, text width or height, line or paragraph spacing, document font,
  chapter openings or running headers. This includes:
  - `\geometry`, `\setlength{\textwidth…}` and `\setlength{\parskip|\parindent}`;
  - `\linespread`, `setspace`, `fancyhdr`, `titlesec`, `\fontsize`;
  - KOMA-Script commands (`\KOMAoptions`, `\typearea`, `\areaset`,
    `\setkomafont`, `\RedeclareSectionCommand`);
  - `\renewcommand{\cleardoublepage}`;
  - `\PassOptionsToClass{…}{tmdei-style}`, except the two variant hooks in
    `main.tex`.

**Out of scope:** other documents in `report/` with their own
`\documentclass`, i.e. the Extended Abstract (`resumo-alargado.tex`). It keeps
its own options (`oneside`, `british`) on purpose; `FC` skips it, and its page
limit is checked by `abs-check` (skill `abstract`).

**Allowed local fixes**, without changing the layout:

| Problem | Fix |
|---|---|
| `OVERFULL` (text in the margin) | reword or reorder the sentence; add a hyphenation hint (`jurí\-dico`); for URLs, the bibliography already breaks anywhere (`biburl*penalty` in `main.tex`); in text use `\url{}` |
| `UNDERFULL` (badly spaced line) | usually info; reword if it is visible in the body text |
| `MARGIN` | same as `OVERFULL`; wide tables/figures: `\resizebox{\linewidth}{!}{…}` or a smaller `\small` table font, never a wider text block |
| `HEADING-AT-BOTTOM` | reword the previous paragraph; if that does not help, record the case and leave it. Never `\newpage` or `\enlargethispage`, and do not load `needspace` or other page-break packages |
| `FLOAT` | use `[htbp]`, reduce the float size, or move the float source next to its first reference. Floats drifting to the end of a chapter are not detected: look for them |
| `CHAPTER-PARITY` | a chapter starts on an even page: something removed `openright` (a class option or a KOMA command). Undo it; never add a manual `\cleardoublepage` |
| `EMPTY-LIST` | comment the list command in `frontmatter.tex` until there is something to list; uncomment it when the first figure/table appears |
| `BLANK-PAGE` (print) | expected only before a chapter-level start on an odd page; anything else means a manual break — remove it |
| `PAGE-NUMBER` | means a `\thispagestyle`/`\pagestyle` change — remove it |

**Manual page breaks** (`\newpage`, `\clearpage`, `\pagebreak`) and
`\pagestyle` are warnings, because the template places chapters itself. A line
copied from the template, or a justified exception, may end in
`% formatacao: <reason>`. That makes it an info `EXEMPT` finding, and the
reason must also be in the PR.

Only warnings can be exempted. Error-level commands (margins, spacing, font,
KOMA-Script, class options) are reported even with the marker.

**Updating the reference**: if the upstream template changes:

1. Compare the new class and options with the pinned commit.
2. Copy the new files.
3. Update the hashes and commit in `referencia-modelo.txt` in the same PR,
   explaining what changed.

Never update the hashes to silence a local edit.

## Done when

- `FC` exits `0` (or `3` with every warning decided) for both formats of the
  version being released, and LaTeX reports 0 errors.
- You looked at the changed pages in both PDFs.
- The final review is done, or reported as incomplete (`AGENTS.md`, «Skills»; step 5). When another skill runs this one, its review covers this step.
- You reported the results per format, and any `EXEMPT` lines with their reason.
