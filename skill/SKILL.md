---
name: academic-tree-reproduction
description: Reproduce an AcademicTree academic genealogy, enrich its authors and publications with OpenAlex and DBLP, and generate an offline left-to-right interactive HTML tree. Use whenever a user asks for academic genealogy, advisor trees, academic inbreeding, or author-network publication enrichment.
---

# Academic Tree Reproduction

Use the bundled scripts to collect a public AcademicTree genealogy, enrich nodes with OpenAlex works and optional DBLP records, and build an offline HTML visualization.

## Workflow

### Verified public-page fallback (preferred for the Hinton example)

The tree endpoint is readable while `peopleinfo.php` may return HTTP 200 with a Turnstile body. Detect the body, not only HTTP status. Never treat an HTML challenge as an author record.

Save the public tree response at `outputs/academictree-access-evidence/tree.html`, then run `scripts/public_pipeline.py` from the delivery workspace and `scripts/build_public_html.py`. These are the currently verified pipeline; the older prototype scripts below are not validated for complete genealogy traversal. The pipeline requires Python with lxml and curl. It extracts node names from the name font, not all anchor descendant text, because malformed legacy markup can nest student tables inside an anchor. Ancestor edges follow nested tables; descendant edges follow enclosing `div<PID>` branches. Preserve multi-parent edges and label them as training relationships rather than assuming PhD supervision.

For another scholar pass `--tree-url`, `--tree-html`, `--output`, and optionally `--root-query` and a reviewed `--root-author-id` to public_pipeline.py. Do not reuse Hinton's ID for other roots. Use build_case.py with --case, --root and --title for a separate offline page. If AcademicTree search is challenged and no verified PID is found, report genealogy unavailable; an OpenAlex-only author page is not a genealogy reproduction. Record the rate-limit response before and after each sequential experiment, remove api_key from the recorded response, and distinguish network errors from quota exhaustion.

OpenAlex responses and all work pages are cached in `data/source-records`. Match names against variants, reject ambiguous candidates, and record pagination failure separately from zero works. Hinton's author ID A5108093963 is verified. Name-only matches for other nodes remain provisional and require review; institutions are supporting evidence, not proof of PhD institution. Full source work fields are preserved in `works.raw.json` and the normalized records. The saved public page is a bounded snapshot, not proof of exhaustive descendants.

The viewer template in `scripts/viewer.html` supports horizontal generation layout, pan/zoom, search, author selection, year filters, citation sorting, all-field inspection and explicit missing-data status. Gray nodes are unmatched. Never report the project complete solely because a one-node HTML file exists.

If OpenAlex reports an insufficient shared IP budget, stop new uncached searches and mark affected authors `api_error`. Do not call them `not_found`. The pipeline accepts `OPENALEX_API_KEY` from the environment for resumed requests; never embed it in the HTML or deliverables. Successful cached responses are reused, while error responses may be retried on the next run.

1. Run `crawl_academic_tree.py` with a public tree and PID. Use `--ancestors 4`, `--resume`, a cache directory, and a respectful `--rate-limit` (default 10 seconds for AcademicTree).
2. Run `enrich_openalex.py` on `nodes.json`. It searches authors, keeps the selected OpenAlex author record, and paginates all works.
3. Run `enrich_dblp.py`. Treat non-JSON validation pages as `blocked`; never bypass them.
4. Run `merge_records.py` and `build_html.py`.
5. Read `manifest.json` and report missing, blocked, and ambiguous records.

Preserve raw source responses, source URLs, matching method, and confidence. Never claim that database coverage equals a complete real-world publication history. Keep multiple advisor edges and cross-tree IDs. OpenAlex cited-by counts are the color metric; publication count is the node-size metric.

## Output contract

For a multi-scholar website, use scripts/gallery.html as the tab shell and build each scholar under trees/<case> with its own root/title/data. Load each frame only on first selection and keep it mounted to preserve zoom, position and cached detail data. Preserve source/completeness notes per tab, including unprocessed family members. Hash links select the scholar. Do not download all datasets on initial page load.

### Cross-scholar troubleshooting verified with Tao

AcademicTree search/peopleinfo may return a Turnstile page even with HTTP 200, while tree.php can be readable. First locate a verified PID via public sources; never guess PID values. If no AcademicTree identity is verifiable, an independent genealogy source can be used with its own namespace. For Tao the public Mathematics Genealogy Project page `https://www.genealogy.math.ndsu.nodak.edu/id.php?id=43967` explicitly gives Elias Menachem Stein as advisor, Princeton PhD 1996, and 25 direct students in the saved 2026-10-14 response. Parse advisor paragraphs and student rows only; do not infer all descendants. Preserve MGP attribution and exact source URLs. The accompanying `repair_tao.py` is a saved-case adapter, not a general MGP crawler. Do not bulk crawl MGP without checking its access rules.

A failed TLS request is a transport failure, not proof the page is absent or protected. Retry normal verified HTTPS clients or another official source; do not disable certificate verification. If the official award snapshot remains unavailable, record it as unavailable and do not claim it was recovered merely because genealogy succeeded.

Use `build_case.py --case <folder> --root <namespaced-id> --title <title>` for offline HTML. For web output use `build_pages.py --data <data-folder> --output <site-folder> --root <id> --title <title>`; root/title may also come from manifest. Both renderers substitute all legacy root references including reset/centering, and label source links using node source_name/tree. Do not publish another scholar under Hinton's heading or reset target. Unprocessed family members are not zero-publication authors. Check generated title, source link, root selection, reset, and first displayed author for each new case.

For web publication run `scripts/build_pages.py`: it writes `outputs/cloudflare-pages-progressive` and its ZIP. Serve graph.bin first (nodes, relationships, work counts/citation summary), then fetch compressed author details only on selection. Preserve the current viewer/force/interaction templates, deduplicate concurrent detail loads, reject stale panel updates and allow retry. Keep the offline single-file build separate. Do not reintroduce downloading all work metadata before graph render.

Run `scripts/audit_nodes.py --data <data-directory>` after acquisition. Deliver node-status.json, node-status.csv and append-only acquisition-log.jsonl. Retrieval completeness requires matched author, terminal pagination, known expected count equal to unique retrieved count, no duplicate IDs and all work records present. Keep identity verification and all-source completeness separate. Preserve failures and source error bodies. Never equate missing details or quota errors with zero works. The main public pipeline invokes the audit automatically.

For offline acquisition use the official complete OpenAlex snapshot, stream JSONL.gz or Parquet, and filter authors/works locally by verified author IDs. Record snapshot date, corpus inclusion and whether every shard was scanned; partial shard downloads cannot prove completeness. A saved API response still uses API budget. Use one owner-authorized personal or organization key; the official free key raises the anonymous daily budget tenfold, and paid plans are available. Do not create or rotate multiple free accounts to pool or evade quotas. The official docs do not state that such pooling is supported. Keep `OPENALEX_API_KEY` local and out of logs and deliverables.

Create `data/nodes.json`, `edges.json`, `authors.json`, `works.json`, `manifest.json`, and a single offline HTML file. Include a Chinese methods document when delivering results to Chinese-speaking users.
