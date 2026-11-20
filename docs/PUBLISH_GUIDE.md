# Publish guide (first-timer friendly)

*Do this only after the verification checklist is complete and the publish gate passes. Total time: about 45 minutes. Nothing here was pushed automatically, because no GitHub or Zenodo token was supplied.*

## Copy-ready text

- **Repository name:** `greensand-nir`
- **Repository description:** Open near-infrared reference library and detection-limit benchmark for foundry green sand additive control
- **Author line:** Maurice Kuubata, Independent Researcher, Dubuque, Iowa, USA, ORCID 0009-0003-3178-5971
- **Keywords:** near-infrared spectroscopy; foundry; green sand; seacoal; iron oxide; spectral library; detection limit; chemometrics

## Step 1: Zenodo account (3 min)

Go to https://zenodo.org/signup/ and choose **Log in with ORCID**. Your ORCID then attaches to every record.

## Step 2: GitHub repository (10 min)

1. Go to https://github.com/new. Name: `greensand-nir`. Public. Do **not** add a README (the project has one). Click **Create repository**.
2. In a terminal inside the project folder:
   ```
   git init -b main
   git add -A
   git commit -m "Green Sand NIR Reference Library v1.0.0"
   git remote add origin https://github.com/mauricekuubata/greensand-nir.git
   git push -u origin main
   ```
   The screen should end with `main -> main`.
3. Leaderboard page: on GitHub, **Settings > Pages > Source: Deploy from a branch > main > /docs > Save**. After a minute the page is at https://mauricekuubata.github.io/greensand-nir/leaderboard/

## Step 3: Four Zenodo records (25 min)

Build the four upload archives first:
```
python code/08_release_archives.py
```
This writes `release/greensand-nir-library-v1.0.0.zip`, `-benchmark-`, `-moisture-` and `-software-` zips. For each:

1. Zenodo > **New upload**. Drag in the zip.
2. Fill in from `zenodo/<name>.json` (title, description, upload type, license, keywords, version 1.0.0). Creator: Kuubata, Maurice, ORCID 0009-0003-3178-5971, affiliation "Independent Researcher, Dubuque, Iowa, USA".
3. Related identifiers: the GitHub URL ("is supplement to"), 10.5066/F7RR1WDJ ("is derived from").
4. Click **Publish**. Copy the DOI shown (looks like 10.5281/zenodo.1234567).

Alternative for the software record: Zenodo > **Account > GitHub**, flip the switch for `greensand-nir`, then on GitHub **Releases > Draft a new release**, tag `v1.0.0`, publish. Zenodo mints the software DOI automatically.

Faster, if you prefer: create a Zenodo token (https://zenodo.org/account/settings/applications/tokens/new/, tick deposit:write and deposit:actions) and a GitHub token (https://github.com/settings/tokens, tick "repo"), give them to Claude in a new session, and it will push to the Zenodo sandbox first so you can see the result, then for real. Revoke both tokens afterwards.

## Step 4: Record the DOIs (5 min)

Paste each DOI into `CITATION.cff` (doi field), the README status line, and `docs/evidence_log.csv`, then commit and push. Save a PDF of each Zenodo record page.

## Preprint (20 min)

The preprint is `paper/preprint/main.pdf`; its LaTeX source bundle is `paper/preprint/preprint_source.zip` (main.tex, main.bbl, refs.bib, macros.tex, tables/, figures/).

- **engrXiv** (https://engrxiv.org, engineering; no endorsement needed): create an account, Submit, upload `main.pdf`, paste the title and abstract from the PDF, add the GitHub URL and the four Zenodo DOIs as related resources, choose CC BY 4.0, and complete the AI-use statement with the text in the paper's "Author contributions and use of AI tools" section.
- **arXiv** (https://arxiv.org/submit; category physics.app-ph is the closest fit): first-time submitters need an endorsement in the category (https://arxiv.org/auth/endorse); ask a former advisor or co-author who posts there. Upload `preprint_source.zip`, title and author exactly as in the PDF, license CC BY 4.0, comments "13 pages, 10 figures; data and code at github.com/mauricekuubata/greensand-nir".
- After posting, record the preprint ID or DOI in `docs/evidence_log.csv` and the README.

## Optional: PyPI (10 min)

Create an account at https://pypi.org, make an API token, then `python -m build` and `python -m twine upload dist/*` (username `__token__`, password = token).

## Optional: Journal of Open Source Software

`paper/paper.md` is a draft. JOSS expects substantial, tested, documented software; submit at https://joss.theoj.org/papers/new with the repository URL and the software DOI after the package has been public for a while and you have rewritten the paper in your own words.
