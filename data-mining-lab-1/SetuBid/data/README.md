# SetuBid Data Directory

This directory is reserved for tender notices and evaluation datasets.
By default, the pipeline reads input data from either the local `./data/` directory or from `../exam/data_2/`.

### Expected files:
- `notices/*.parquet`: Directory containing Apache Parquet files of scraped procurement notices.
- `labelled_pairs.csv`: Ground-truth pairwise adjudication file with columns `notice_id_a`, `notice_id_b`, `label`.
- `portal_profiles.md`: Qualitative notes and metadata regarding portal scraping idiosyncrasies and boilerplate.

Note: Raw notice files and database binary dumps should not be committed to version control.
