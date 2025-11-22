import asyncio
import pandas as pd
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import os
import time
import random

class AviationScraper:
    def __init__(self, start_year=1919, end_year=2025, output_file="aviation_accidents.csv"):
        self.start_year = start_year
        self.end_year = end_year
        self.output_file = output_file
        self.base_url = "https://aviation-safety.net"
        self.data = []
        # Check if file exists to append or create new
        if os.path.exists(self.output_file):
            print(f"Found existing file {self.output_file}, appending new data.")
        else:
            # Create empty file with headers if not exists
            df = pd.DataFrame(columns=[
                "Date", "Time", "Type", "Owner/operator", "Registration", "MSN", 
                "Year of manufacture", "Fatalities", "Other fatalities", "Aircraft damage", 
                "Category", "Location", "Phase", "Nature", "Departure airport", 
                "Destination airport", "Confidence Rating", "Narrative", "Source URL"
            ])
            df.to_csv(self.output_file, index=False)

    async def setup_browser(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False) # Headless=False to see what's happening and avoid some bot detection
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.page = await self.context.new_page()

    async def close_browser(self):
        await self.browser.close()
        await self.playwright.stop()

    async def scrape(self):
        await self.setup_browser()
        try:
            for year in range(self.start_year, self.end_year + 1):
                print(f"Scraping year: {year}")
                await self.scrape_year(year)
                # Save progress after each year
                self.save_data() 
                self.data = [] # Clear memory
        finally:
            await self.close_browser()

    async def scrape_year(self, year):
        page_num = 1
        while True:
            url = f"{self.base_url}/database/year/{year}/{page_num}"
            print(f"  Processing {url}")
            try:
                response = await self.page.goto(url, timeout=60000)
                if response.status == 404:
                    print(f"  Page {page_num} not found for year {year}. Moving to next year.")
                    break
                
                content = await self.page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Check if there are accidents listed. 
                # The list is usually in a table or list. 
                # Based on exploration, we look for links to /wikibase/ or /database/record.php
                # Let's look for the main table.
                
                # If the page says "No accidents found" or similar, break.
                if "No accidents found" in content: # Adjust based on actual text
                     break

                # Find accident links
                # Usually in a table with class 'events' or similar, or just look for specific link patterns
                # The links look like <a href="/wikibase/561999">...</a>
                
                links = []
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if href.startswith('/wikibase/') or href.startswith('/database/record.php'):
                        # Avoid duplicates and non-accident links if any
                        if href not in links:
                            links.append(href)
                
                if not links:
                    print(f"  No accident links found on page {page_num}. Ending year {year}.")
                    break

                print(f"  Found {len(links)} accidents on page {page_num}")
                
                for link in links:
                    full_link = self.base_url + link
                    await self.scrape_accident(full_link)
                    await asyncio.sleep(random.uniform(1, 3)) # Rate limiting

                # Check for next page
                # If we just iterate page_num, we need to know when to stop.
                # If the current page had links, we try the next page.
                # However, some years might define pagination explicitly.
                # Assuming /year/YYYY/N format works and returns 404 or empty list when done.
                
                page_num += 1
                await asyncio.sleep(random.uniform(2, 5))

            except Exception as e:
                print(f"  Error processing year {year} page {page_num}: {e}")
                break

    async def scrape_accident(self, url):
        print(f"    Scraping accident: {url}")
        try:
            await self.page.goto(url, timeout=60000)
            content = await self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            record = {"Source URL": url}
            
            # Extract fields based on "Label: Value" structure
            # Labels are in <b> tags
            
            # Helper to get text after a label
            def get_field(label):
                # Case 1: Table row
                td_label = soup.find('td', class_='caption', string=lambda text: text and label in text)
                if td_label:
                    next_td = td_label.find_next_sibling('td')
                    if next_td:
                        return next_td.get_text(strip=True)
                
                # Case 2: Span (Narrative) - usually handled separately but check here just in case
                return None

            record["Date"] = get_field("Date:")
            record["Time"] = get_field("Time:")
            record["Type"] = get_field("Type:")
            record["Owner/operator"] = get_field("Owner/operator:")
            record["Registration"] = get_field("Registration:")
            record["MSN"] = get_field("MSN:")
            record["Year of manufacture"] = get_field("Year of manufacture:")
            record["Fatalities"] = get_field("Fatalities:")
            record["Other fatalities"] = get_field("Other fatalities:")
            record["Aircraft damage"] = get_field("Aircraft damage:")
            record["Category"] = get_field("Category:")
            record["Location"] = get_field("Location:")
            record["Phase"] = get_field("Phase:")
            record["Nature"] = get_field("Nature:")
            record["Departure airport"] = get_field("Departure airport:")
            record["Destination airport"] = get_field("Destination airport:")
            record["Confidence Rating"] = get_field("Confidence Rating:")
            
            # Narrative extraction
            narrative_label = soup.find('span', class_='caption', string=lambda text: text and "Narrative:" in text)
            if narrative_label:
                narrative_text = ""
                curr = narrative_label.next_sibling
                while curr:
                    if curr.name == 'div' and 'captionhr' in curr.get('class', []): # Stop at next section header
                        break
                    if curr.name == 'br':
                        narrative_text += "\n"
                    elif curr.name == 'span':
                        narrative_text += curr.get_text(strip=True)
                    elif isinstance(curr, str):
                        narrative_text += curr
                    curr = curr.next_sibling
                record["Narrative"] = narrative_text.strip()

            self.data.append(record)
            
            # Save every 10 records
            if len(self.data) >= 10:
                self.save_data()
                self.data = [] # Clear memory

        except Exception as e:
            print(f"    Error scraping accident {url}: {e}")

    def save_data(self):
        if not self.data:
            return
        
        new_df = pd.DataFrame(self.data)
        # Append to CSV
        new_df.to_csv(self.output_file, mode='a', header=False, index=False)
        print(f"    Saved {len(self.data)} records to {self.output_file}")

if __name__ == "__main__":
    scraper = AviationScraper(start_year=1919, end_year=2025)
    asyncio.run(scraper.scrape())
