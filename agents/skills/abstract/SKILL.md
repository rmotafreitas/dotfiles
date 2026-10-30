---
name: abstract
description: Use whenever you write, update or review the dissertation's abstracts — the report's Resumo (PT-PT) and Abstract (EN-GB) in report/frontmatter/frontmatter.tex, and the PREPD Extended Abstract (report/resumo-alargado.tex, due 16/12/2026) — or when the user asks for a summary of the work ("abstract", "resumo", "resumo alargado", "extended abstract", "palavras-chave", "keywords").
---

# abstract

Three texts, one synthesis of the same work:

| Text | Where | Language | Limit |
|---|---|---|---|
| Resumo | `report/frontmatter/frontmatter.tex`, `\begin{abstract}` | PT-PT, academic | ≤ 200 words (template guide) |
| Abstract | same file, `\begin{abstractotherlanguage}` inside `\begin{otherlanguage}{british}`, ending with `{\bf Keywords:} …` | **British English** | ≤ 200 words |
| Extended Abstract | `report/resumo-alargado.tex` → `make docker-resumo-alargado` → `report/resumo-alargado.pdf` | British English | `formato.txt` |

The limits, sections and language come from `formato.txt`.

- **The Extended Abstract format there is a provisional default**: no available document defines it. When the PREPD FAQ or the advisor gives the real format, update `formato.txt` (and `alargado fonte`). Then update the document's structure.
- **English is an explicit exception to the PT-PT rule in `AGENTS.md`**: it applies only to these two texts.

`AC` below means `.agents/skills/abstract/scripts/abs-check`. Run it from the repo root (it is not on `PATH`).

## What an abstract is here

A PREPD is a **proposal**. The abstracts describe:

- context and problem;
- the research questions;
- the planned method;
- the **expected** contributions (and, for the Extended Abstract, the work plan).

They never report results, conclusions or numbers that the report does not contain. When a chapter is still `\todo`, describe what is planned, as Chapter 1 does; do not fill the gap.

## Procedure

1. **Read everything the abstracts must reflect**:
   - `report/ch*/` (Chapter 1 above all, and the method in Chapter 2);
   - `report/frontmatter/glossary.tex`;
   - `research/sources.md`, `research/protocolo-pesquisa.md` and `research/snowball-qi*.md`.

   External documents (the formalization, course PDFs) are not in the repo and are not sources.
2. **Write or update all three texts together**, so that they say the same thing:
   - Resumo first, then Abstract.
   - Resumo and Abstract have the same paragraphs, in the same order: context and aim → research questions → method and expected contributions.
   - The Extended Abstract has the sections in `formato.txt`.
   - Keywords: at most 6, in `\keywords{…}` in `main.tex` (Portuguese) and in the Abstract's `{\bf Keywords:}` line (the same terms, translated, same order).
   Then run `AC` once (step 4): its errors (words, keywords, commands,
   sections) are structural, so fix them before the language passes.
3. **Run the other skills, in this order**, without their own review step (the
   review in step 5 covers them):
   1. `glossario`: no `\gls`/`\acr*` in any of the three texts. Write the terms in full; in the Extended Abstract, give an acronym in full on its first use. `gls-check` must have no `ABSTRACT` error.
   2. `pesquisa-bibliografica`:
      - the Resumo and Abstract have **no citations**;
      - the Extended Abstract may cite, but only sources already registered and verified;
      - every number must come from such a source and already appear in the report (`AC` warns with `NUMBER`).
   3. `revisao-pt-pt`, on the Resumo:
      ```sh
      .agents/skills/revisao-pt-pt/scripts/lt-check --env abstract report/frontmatter/frontmatter.tex
      ```
   4. English check, on the Abstract and the Extended Abstract:
      ```sh
      .agents/skills/revisao-pt-pt/scripts/lt-check --lang en-GB --env abstractotherlanguage report/frontmatter/frontmatter.tex
      .agents/skills/revisao-pt-pt/scripts/lt-check --lang en-GB report/resumo-alargado.tex
      ```
      Then apply the English checklist below.
   5. `formatacao`: build (`make docker-ambos` and `make docker-resumo-alargado`) and run `fmt-check` on the report PDFs. Each of the Resumo and the Abstract must fit on one page (no script checks this; each title must share its page with its keyword line):
      ```sh
      for p in $(seq 1 15); do pdftotext -f $p -l $p report/main.pdf - | grep -o -E '^(Resumo|Abstract)$|Palavras-chave|Keywords' | sed "s/^/p. $p: /"; done
      ```
      The Extended Abstract body must fit in the `formato.txt` page limit (`AC` checks this).
4. **Run `AC`** until it has no errors (again at the end, as the final gate):
   ```sh
   .agents/skills/abstract/scripts/abs-check
   ```
   Exit codes: `0` clean; `3` warnings to decide; `1` errors; `2` bad input.
   Add `--sem-alargado` to skip the Extended Abstract.
5. **Review the texts** with `sol-loop` (GPT Sol, iterating) and then `council` (Claude Opus, GPT Sol, GPT Luna), as every custom skill does (`AGENTS.md`, «Skills»). All reviewers are read-only.
   - Brief them with the three texts, the report and the PREPD criteria. Ask them to check: fidelity to the report (nothing invented), PT-PT and British English quality, the same content in both languages, and the limits, plus the review focus of each skill run in step 3.
   - Do this on every run, and again before each delivery (16/12 Extended Abstract; 06/01 report).
6. **Report**:
   - word counts;
   - `AC`, `lt-check` and `fmt-check` results;
   - what changed;
   - anything left as provisional, such as the Extended Abstract format;
   - the review outcome (rounds and scores).

## English checklist (British, academic)

- **Spelling:** British spelling with *-ise* (*organise*, *characterise*, *utilisation*). Also *behaviour*, *modelling*, *centre*, *analyse*. `lt-check --lang en-GB` reports `EN_US_SPELLING`/`EN_IZE`.
- **Serial comma:** none (house style). The serial-comma rule is disabled in `lt-check`.
- **Voice:** impersonal or third person (*this work proposes*, *the study compares*). No *I*/*my*, no contractions.
- **Tense:**
  - present for what the dissertation does and the state of the art;
  - future or *is expected to* for planned work and contributions;
  - never past tense for work not yet done.
- **Numbers:** decimal point (*28.5%*), with the thousands separator being a comma or thin space (*456,000*). Avoid figures that the report does not state.
- **Terms:** use the standard English term, not a calque. For example: *large language model*, *time series forecasting*, *root mean squared error* (FPP3), *decision support*, *charging station*, *research question*.
- **False friends:** off by default in `lt-check`. When in doubt, check them with `--falsos-amigos`.
- **Language setting:** use babel's `british`, never `english` (US hyphenation and US dates such as «10/29/2026» in the references). The Abstract is inside `otherlanguage{british}` and the Extended Abstract uses the `british` class option. Keep both.

## Done when

- `AC` has no errors.
- The language checks show no unexplained finding, `gls-check` and `fmt-check` have no errors, and `verify-bib --cited report` meets the rule in `pesquisa-bibliografica` (exit 0, or 3 with every manual check recorded).
- The final review is done, or reported as incomplete (`AGENTS.md`, «Skills»; step 5). When another skill runs this one, its review covers this step.
- You reported the counts, the results and what is still provisional.
