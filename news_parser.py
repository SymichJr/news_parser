import os
import random
import sqlite3
import time
from datetime import datetime
from multiprocessing import Pool

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver

load_dotenv()

PATH_TO_DRIVER = os.getenv("PATH_TO_DRIVER")
random_delay = time.sleep(random.randint(5, 10))


def create_db():
    conn = sqlite3.connect("profile.db")
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS Cookie_Profile
              (id INTERGER PRIMARY KEY NOT NULL,
              created_at TIMESTAMP NOT NULL,
              cookie_value TEXT,
              last_run TEXT,
              total_runs INTEGER DEFAULT 0)"""
    )
    for i in range(1, 16):
        c.execute(
            f"""INSERT OR IGNORE INTO Cookie_Profile (id, created_at)
                VALUES (?, datetime('now', 'localtime'))""",
            (i,),
        )
    conn.commit()
    conn.close()


def get_news_links():
    url = "https://news.google.com/home"
    responce = requests.get(url)
    soup = BeautifulSoup(responce.text, "html.parser")
    new_links = []
    if responce.status_code == 200:
        for link in soup.select("a"):
            href = link.get("href")
            if href and href.startswith("./articles/"):
                new_links.append("https://news.google.com" + href[1:])
    return new_links


def selenium_cookies(profile):
    conn = sqlite3.connect("profile.db")
    c = conn.cursor()
    c.execute("SELECT cookie_value FROM Cookie_Profile WHERE id=?", (profile,))
    cookie = c.fetchone()[0]
    options = webdriver.ChromeOptions()
    if cookie:
        options.add_argument(f"--cookie={cookie}")
    driver = webdriver.Chrome(options=options, executable_path=PATH_TO_DRIVER)
    links = get_news_links()
    driver.get(random.choice(links))
    random_delay
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
    random_delay
    cookies = driver.get_cookies()
    cookie_value = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
    last_run = str(datetime.now())
    c.execute(
        """UPDATE Cookie_Profile SET cookie_value=?,
           last_run=?, total_runs=total_runs+1 WHERE id=?""",
        (cookie_value, last_run, profile),
    )
    conn.commit()
    conn.close()
    driver.close()


def profile():
    conn = sqlite3.connect("profile.db")
    c = conn.cursor()
    profiles = [row[0] for row in c.execute("SELECT id FROM Cookie_Profile")]
    pool = Pool(processes=5)
    pool.map(selenium_cookies, profiles)


def main():
    create_db()
    profile()


if __name__ == "__main__":
    main()
