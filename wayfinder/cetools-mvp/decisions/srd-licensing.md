---
title: SRD licensing and redistribution obligations
status: resolved
type: research
blocked-by: []
---

## Question

What license governs the Cepheus Engine SRD content published at
https://evolvedexperiment.github.io/cepheus-srd/, and what obligations
does it impose on shipping SRD-derived table data (careers, skills,
equipment, task rules) inside an open-source Python package distributed
on PyPI? Specifically: required attribution and license text, any
Product Identity or trademark restrictions on naming, and whether
verbatim table text may be embedded in the package's data files.

## Resolution

Researched 2026-08-11 from the SRD site's legal page and source
repository.

**License: Open Game License v1.0a** (not Creative Commons). "All of the
text in this document is designated as Open Gaming Content", except the
Product Identity carve-outs: Samardan Press product titles and the
trademarks "Cepheus Engine" and "Samardan Press". The repo's LICENSE
also places its HTML scaffolding under the Unlicense, but that covers
only the site's markup, never the game text.

**Verbatim table content may ship in the package's data files.** OGL
Section 4 grants copying, editing, reformatting, and distribution of all
Open Game Content; no paraphrasing is required. The SRD contains no
closed Mongoose/FFE content.

**Obligations when distributing SRD-derived data on PyPI:**

- Bundle the full OGL 1.0a text (e.g. `LICENSE-OGL.txt`) in both sdist
  and wheel, not just a link.
- Reproduce the SRD's entire Section 15 copyright-notice chain verbatim
  (WotC 2000 through "Cepheus Engine System Reference Document,
  Copyright © 2016 Samardan Press; Author Jason 'Flynn' Kemp"), then
  append our own line for the package's game data.
- Clearly designate which parts are Open Game Content: the game-data
  files are OGC under OGL 1.0a only (they cannot be sublicensed
  MIT/CC); the Python code is independent and takes whatever software
  license we choose. Mixed licensing is standard practice.
- Keep the Product Identity strings "Cepheus Engine" and "Samardan
  Press" out of the shipped OGC data files.

**Naming and trademark:** "Cepheus Engine" is claimed Product Identity;
naming the package with it (e.g. `cepheus-engine-tools`) is risky and
not among the uses the Compatibility-Statement License (CSL) permits.
The CSL does expressly permit describing the package as "compatible with
the rules of Cepheus Engine" provided the README/PyPI description carry
the trademark attribution ("Cepheus Engine and Samardan Press are the
trademarks of Jason 'Flynn' Kemp") and a non-affiliation statement. The
bare word "Cepheus" is not a declared mark and is widely used by
third-party products; `cetools` avoids the question entirely.

**Implication for [Rules data schema](rules-data-schema.md):** no
constraint on format or fidelity; tables may be encoded verbatim. The
schema work is unblocked. Packaging obligations (license files, Section
15, OGC designation, CSL statement) fold into
[Library and CLI architecture](library-cli-architecture.md) and the
eventual packaging feature.

Sources: [SRD legal page](https://evolvedexperiment.github.io/cepheus-srd/legal.html),
[EvolvedExperiment/cepheus-srd LICENSE](https://github.com/EvolvedExperiment/cepheus-srd/blob/master/LICENSE),
[upstream orffen/cepheus-srd](https://github.com/orffen/cepheus-srd).
