import requests
import re
from bs4 import BeautifulSoup
import json
import pandas as pd
import logging
import traceback
import sys
import os
import re
from datetime import datetime

application_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(
    os.path.abspath(__file__))
os.chdir(application_path)

# Configure logging
logging.basicConfig(
    filename='hamden_agendacenter.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.ERROR
)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
}


def clean_text(text):
    text = re.sub(r'[\s]+', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()


def main():
    try:
        print('Downloading webpage...')
        r = requests.get('https://www.hamden.com/agendacenter', headers=headers)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, 'html.parser')
    except requests.RequestException as e:
        logging.error(f"Request failed: {e}")
        logging.error(traceback.format_exc())
        return

    all_records = []

    try:
        print('Parsing webpage...')

        for cat_div in soup.select('div[id^="cat"]'):
            category_name = cat_div.select_one('h2[onclick*="expandCollaspseCategory("]')
            category_name = category_name.get_text(strip=True) if category_name else "Unknown"

            for tr in cat_div.select('tr[class="catAgendaRow"]'):
                date_header = None

                for h in ['h4', 'h1', 'h2', 'h3', 'h5', 'h6']:
                    date_header = tr.select_one(h)
                    if date_header and date_header.find('strong'):
                        break

                if not date_header:
                    continue

                meeting_date = date_header.select_one('strong')
                meeting_date = clean_text(meeting_date.extract().text) if meeting_date else ""
                if not meeting_date:
                    continue

                posted_or_amended = re.search('(?:Posted|Amended)(.+)', clean_text(date_header.text), flags=re.I | re.S)
                if not posted_or_amended:
                    posted_or_amended = "NOT POSTED"
                else:
                    posted_or_amended = posted_or_amended.group(1)
                    if 'Amended' in meeting_date:
                        posted_or_amended = f"A - {posted_or_amended}"

                meeting_title = tr.select_one('p a[id][href*="ViewFile"]')
                meeting_title = clean_text(meeting_title.text)
                if not meeting_title:
                    continue
                all_records.append({
                    "Category": category_name.replace('▼', '').strip(),
                    "Title": meeting_title,
                    "Date": meeting_date,
                    "Posted/Amended": posted_or_amended
                })
    except Exception as e:
        logging.error(f"Error while parsing webpage: {e}")
        logging.error(traceback.format_exc())
        return

    try:
        try:
            sorted_records = sorted(all_records, key=lambda x: datetime.strptime(x['Date'], '%b %d, %Y'), reverse=True)
            all_records = sorted_records
        except:
            pass

        print('Writing CSV and JSON...')
        df = pd.DataFrame(all_records)
        df = df.astype(str)
        df.to_csv('Agendas.csv', index=False, encoding='utf-8-sig')
        print('CSV and JSON written successfully!')
    except Exception as e:
        logging.error(f"Error writing files: {e}")
        logging.error(traceback.format_exc())


if __name__ == "__main__":
    main()
