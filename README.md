The main.py a Python script that uses the Playwright library to automate browser interactions, specifically for scraping data from Google Maps. Here is a summary of the key components:

**Logging:**

A logging setup (logs()) is defined to log messages to both the terminal and a file named scrape.log.
Timer Decorator:

A timer decorator (timer()) is used to log the execution time of functions.

**Data Classes:**

**Resturants:**  Defines the structure to store restaurant data.
**SaveData:**  Manages operations to save scraped data in various formats (JSON, CSV, Excel, SQLite).

**GoogleBot Class:**

Initializes with a URL and search query.
**Methods include:**

browser(): Launches the browser and navigates to the URL.

scroll_down(): Handles scrolling on the page.

Type_in_search(): Types the search query into the search bar.

navigate(): Performs search and navigates through the results.

extractor(): Extracts attributes from page elements.

extract_data(): Extracts data from individual restaurant listings.

main(): Orchestrates the overall scraping process.

**Main Execution Block:**
Instantiates and runs the GoogleBot class with a specified URL and search query.
The script is designed to scrape restaurant data from Google Maps, including name, stars, reviews, location, website, and phone number, and save this data in multiple formats.
