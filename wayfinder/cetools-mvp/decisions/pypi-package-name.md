---
title: PyPI package name
status: resolved
type: research
blocked-by: []
---

## Question

Is the name `cetools` available on PyPI? If not (or if it collides with
an established tool), which nearby alternatives are free (for example
`cepheus-tools`, `cepheus-engine`, `cepheustools`)? Are there existing
Cepheus Engine or Traveller-adjacent Python packages whose naming or
scope this project should avoid colliding with?

## Resolution

Researched 2026-08-11 via the PyPI JSON API and web search.

**`cetools` is available on PyPI**, as are `cepheus-tools` and
`cepheustools`. Two candidates are taken:

- `cepheus-engine`: an unrelated, actively maintained container-security
  tool ("Cepheus" by su1ph3r, latest release 2026-06-23). Direct
  collision; avoid.
- `cepheus`: an abandoned cepheid-variable-star analysis tool (last
  release 2018). Also collides conceptually with orffen's GitHub-only
  "Cepheus Engine Toolbox" repo named `cepheus`.

PyPI normalizes `cepheus-tools`/`cepheus_tools`/`cepheus.tools` to one
name; `cepheustools` is distinct.

**Prior art**: no published PyPI package exists specifically for Cepheus
Engine or Traveller tooling; the space is GitHub-only script
collections. Notable neighbors: [orffen/cepheus](https://github.com/orffen/cepheus)
(CE dice/character/world/sector scripts),
[Elured-code/cepheus-python](https://github.com/Elured-code/cepheus-python),
[Elured-code/python-traveller-cl](https://github.com/Elured-code/python-traveller-cl),
[cthulhustig/autojimmy](https://github.com/cthulhustig/autojimmy)
(Mongoose-focused GUI toolkit), and
[xdy/twodsix-foundryvtt](https://github.com/xdy/twodsix-foundryvtt) (the
dominant "Cepheus" brand in the VTT space). None uses the `cetools`,
`cepheus-tools`, or `cepheustools` names.

**Implication**: `cetools` is free and unclaimed by any RPG project, so
the repo name can double as the package name. Final naming (and any
trademark caution around "Cepheus" in a name) is settled in
[Library and CLI architecture](library-cli-architecture.md), informed by
the [SRD licensing](srd-licensing.md) findings.
