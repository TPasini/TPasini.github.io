# tpasini.github.io

Personal website of Thomas Pasini, served by GitHub Pages at https://tpasini.github.io/.

The publication list and the citation figures are refreshed every Monday from NASA ADS by
`.github/workflows/update-publications.yml`, which runs `scripts/update_publications.py`.
It needs an ADS API token stored as the repository secret `ADS_API_TOKEN`.
To refresh by hand: Actions → "Update publications from NASA ADS" → Run workflow.

To hide a paper that ADS wrongly attributes, add its bibcode to `EXCLUDE_BIBCODES` in the script.
