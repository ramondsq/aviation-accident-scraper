# Aviation Safety Network Scraper Walkthrough

I have successfully built a Python scraper to collect aviation accident data from [aviation-safety.net](https://aviation-safety.net/database/).

## Features
- **Comprehensive Data**: Scrapes accidents from 1919 to 2025.
- **Detailed Extraction**: Captures all key fields including Date, Time, Aircraft details, Location, and Narrative.
- **Robustness**: Uses `playwright` to handle dynamic content and potential anti-scraping measures.
- **Resumable**: Saves data incrementally to `aviation_accidents.csv`.

## How to Run

1.  **Install Dependencies**:
    Ensure you have `uv` installed.
    ```bash
    uv sync
    uv run playwright install chromium
    ```

2.  **Run the Scraper**:
    ```bash
    uv run scraper.py
    ```

    The scraper will start from 1919 and progress to 2025. It prints progress to the console.

## Output
The data is saved to `aviation_accidents.csv` in the project directory.
Columns include:
- Date, Time
- Type, Owner/operator, Registration, MSN, Year of manufacture
- Fatalities, Other fatalities, Aircraft damage, Category
- Location, Phase, Nature
- Departure/Destination airport
- Confidence Rating, Narrative
- Source URL

## Notes
- **Execution Time**: Scraping the entire database will take a significant amount of time due to the large number of records and rate limiting (added to be polite and avoid bans).
- **Interruption**: You can stop the script (Ctrl+C) at any time. Since it saves incrementally, you won't lose much data. To resume, you might need to adjust the `start_year` in `scraper.py`.

## Verification Results
I verified the scraper by running it for the year 2025.
- **Data Quality**: Successfully extracted details including complex fields like "Narrative" and "Fatalities".
- **CSV Format**: Confirmed the CSV is well-formed and contains the expected data.
