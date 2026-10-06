# Verification record

Verified on 6 October 2026 using Python 3.12.14 on Windows.

- Installed pinned Python dependencies into a new isolated environment.
- Generated 3,600 related synthetic USD vehicle records with 12 brands and 36 models.
- Trained and compared all three regressors; saved the winning pipeline and JSON metadata.
- Selected Linear Regression: test R² 0.990845, RMSE $926.75, MAE $614.56.
- Seeded the local SQLite database with a hashed demo administrator and 20 labeled records.
- All 37 pytest checks passed with CSRF enabled and isolated SQLite test databases.
- `pip check` reported no broken requirements.
- Started the actual Flask application and tested the public prediction and admin login in Chromium.
- Checked dependent dropdowns, reference specifications, reset, charts, and history search.
- Verified that HTML, CSS, JavaScript, fonts, icons, and the hero image load locally.
- Checked desktop at 1440 × 1000 and mobile at 390 × 844, including history and dataset tables.
- Captured 15 actual application screenshots. Browser checks reported no JavaScript errors or page overflow.
- Checked every screenshot link referenced by the README.
- Replayed setup in a separate clean source checkout with no existing database, secret key, or environment file. Copied `.env.example`, seeded twice (20 records, then 0 additions), ran all 37 tests, and checked persisted authentication and routes.
- Used the already installed isolated Python dependencies for that source-checkout replay; a second dependency installation was not needed.

The runnable local database, generated session key, virtual environment, and temporary verification checkout are excluded by `.gitignore`. GitHub Actions is configured but has not been run on GitHub in this local verification.

Browser details are recorded in [screenshots/verification.json](screenshots/verification.json). The generated decorative car image and its prompt are documented in [hero-image-prompt.txt](hero-image-prompt.txt).

The synthetic test scores and illustrative price band do not establish real market accuracy.
