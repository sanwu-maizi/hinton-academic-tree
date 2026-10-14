# Hinton Academic Genealogy

Interactive academic genealogy with a left-to-right force layout, author search, publication details and citation metrics. Graph data loads first; author records load on demand.

## Cloudflare Pages

### Workers Git deployment

If the connected project shows a deploy command of `npx wrangler deploy`, keep that command and leave the build command empty. Use repository root `/`. The included `wrangler.jsonc` publishes `site` as static assets without a Worker script or API credentials in the repository. The project is deployed as a Workers static asset site; its default URL is on `workers.dev`.

### Pages Git deployment

Connect this repository using Pages Git integration:

- Production branch: `main`
- Framework preset: None
- Build command: leave empty
- Build output directory: `site`
- Root directory: repository root

No API keys or runtime backend are needed. Use HTTPS; opening index.html through file:// cannot load data files.

## Dataset

Public AcademicTree page snapshot for Geoffrey Everest Hinton (PID 1446), enriched using OpenAlex, collected on 2026-10-14. Contains 243 source nodes, 250 training relationships and 11,995 distinct works. 145 nodes have matched author records with complete publication pagination; 85 are ambiguous and 13 have no search match. Name-based matches remain provisional. This is a bounded page snapshot, not an exhaustive genealogy or verified PhD-only network.

AcademicTree author details and DBLP were unavailable. Missing data is not evidence of zero publications. Institutions are not necessarily PhD-awarding institutions. Counts reflect the collection date.

Sources: [AcademicTree](https://academictree.org/computerscience/tree.php?pid=1446), [OpenAlex](https://openalex.org/).

## Attribution

AcademicTree data: The Academic Family Tree, CC BY 3.0; retain attribution and the source link. OpenAlex data: CC0. D3 is distributed under its ISC license; see THIRD_PARTY_NOTICES.md. No blanket license is granted for third-party material beyond its source license.

## Reusable Skill

`skill/` contains collection, audit and visualization scripts. The live site is already built. Regenerating it requires the original collected data and workspace paths described in the skill, which are not included in this compact publication repository. No collection credentials are included.

Local baseline commit: `a857c02`; progressive-loading source commit: `9fe3436`. These refer to the original local repository, not this publication repository.
