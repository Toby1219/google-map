from playwright.async_api import async_playwright, Page, Playwright
from playwright_stealth import stealth_async
import asyncio
from rich.logging import RichHandler
import logging
import inspect
import os, json
import sqlite3
from fake_useragent import UserAgent
from dataclasses import dataclass, asdict, field
import pandas as pd
import functools
import time                                                                                                                         
from openpyxl import load_workbook

def logs():  
    frame = inspect.currentframe().f_back 
    file_name = os.path.basename(frame.f_globals['__file__'])
    logger_name = f"{file_name}"

    logger = logging.getLogger(logger_name)
    logger.setLevel(level=logging.DEBUG)

    terminal = RichHandler()
    logger.addHandler(terminal)
    
    handle = logging.FileHandler("scrape.log", mode='a')
    formats = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    handle.setFormatter(formats)
    logger.addHandler(handle)
   
    return logger

def timer(func):
    @functools.wraps(func)
    async def wrapper(*agrs, **kwargs):
        start = time.perf_counter()
        await func(*agrs, **kwargs)
        end = time.perf_counter()
        total = end - start
        log.info(f"Execution time: {round(total, 2)} seconds...")
    return wrapper

log = logs()

@dataclass
class Resturants:
    Name: str
    Stars: float
    Reviews: str
    Location: str
    Website: str
    PhoneNumber: float

@dataclass
class SaveData:
    file: str = ''
    folder:str = ''
    _path:str = ''
    data_list: list[dataclass] = field(default_factory=list)
   
    def add_item(self, items):
        return self.data_list.append(items)
   
    def create_folder(self):
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)
        self._path = f"{self.folder}/{self.file}"
        return self._path
    
    def dataframe(self):
        return pd.json_normalize((asdict(data) for data in self.data_list), sep='_')

    def save_to_json(self):
        if not os.path.exists(f'{self._path}.json'):
            self.dataframe().to_json(f'{self._path}.json', orient='records', index=False, indent=3)
        else:
            existing_df = pd.read_json(f"{self._path}.json")
            new_df = self.dataframe()
            update_df = pd.concat([existing_df, new_df])
            update_df.to_json(f"{self._path}.json", orient='records', indent=2)

    def save_to_csv(self):
        if os.path.exists(f'{self._path}.csv'):
            self.dataframe().to_csv(f"{self._path}.csv", index=False, mode='a', header=False)
        else:
            self.dataframe().to_csv(f'{self._path}.csv', index=False)
    
    def save_to_excel(self):
        if not os.path.exists(f'{self._path}.xlsx'):
            self.dataframe().to_excel(f'{self._path}.xlsx', index=False)
        else:
            with pd.ExcelWriter(f'{self._path}.xlsx', mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                self.dataframe().to_excel(writer, sheet_name='Sheet1', index=False, header=False, startrow=writer.sheets['Sheet1'].max_row)

    def save_to_sqlite(self):        
        conn = sqlite3.connect(f"{self._path}.db")
        cur = conn.cursor()
        for dats in self.data_list:
            datas = asdict(dats)
            key = [k for k, v in datas.items()]
            keys = ', '.join(key)
            place_holder = ', '.join('?' for _ in range(len(key)))
            values = [json.dumps(v) if isinstance(v, list) else v for v in datas.values()]
            cur.execute(f"CREATE TABLE IF NOT EXISTS scraped (id INTEGER PRIMARY KEY,{keys})")
            cur.execute(f"INSERT INTO scraped ({keys}) VALUES ({place_holder})", (values))
            conn.commit()
            conn.close()

    
    def save_all(self):
        log.info('Saveing data...')
        self.create_folder()
        self.save_to_json()
        self.save_to_csv()
        self.save_to_excel()
        self.save_to_sqlite()
        log.debug('Done saveing...')
        
class GoogleBot:
    def __init__(self, url, search_query="resturant london"):
        self.url = url
        self.page:Page
        self.playwright:Playwright
        self.itemList = []
        self.uniqueItem = []
        self.search = search_query
        
        asyncio.run(self.main())

    async def browser(self)->None:
        log.info("Starting Browser")
        browser = await self.playwright.firefox.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1000, 'height': 600},
            user_agent = UserAgent().random
        )
        self.page = await context.new_page()
        # register the Playwright Stealth plugin
        #await stealth_async(self.page)
        await self.page.goto(self.url,timeout=90000)
    
    async def scroll_down(self):
        """ Handle scrolling """
        log.info("scrolling")
        for _ in range(15):
            await self.page.mouse.wheel(0, 1000)
            await self.page.wait_for_timeout(2000)
    
    async def Type_in_search(self):
        log.info("typing search word")
        try:
            input_search = self.page.locator("input.searchboxinput")
            await input_search.fill(self.search) 
            await self.page.keyboard.press("Enter")
        except:
            log.error("Search bar not found")
            self.page.close()
            time.sleep(5)
            log.info("Found Error closed and now reopening browser")
            await self.main()
                
    async def navigate(self):
        #Type in search bar
        await self.Type_in_search()
            
        await self.page.hover("[role='main']")
        await self.scroll_down()
        listing = self.page.locator("div.id-content-container > #QA0Szd > div > div > div.w6VYqd > div:nth-child(2) >  div > div.e07Vkf.kA9KIf > div > div[role='main'] > div.m6QErb > div[role='feed']")
        
        self.itemList = await listing.locator("a.hfpxzc").all()
        print(len(self.itemList))
        
        for div in self.itemList:
            await div.scroll_into_view_if_needed()
            await div.click()
            await self.extract_data()
            await self.page.wait_for_timeout(6000)

    async def extractor(self, p, s, m):
        try:
            value = await p.locator(s).get_attribute(m)
            return value
        except:
            value = "No data found"
            return value
          
    async def extract_data(self) -> None:
        await self.page.wait_for_selector("div.TIHn2", timeout=13000)
        name = await self.page.locator("h1.DUwDvf").inner_text()
        stars = await self.extractor(p=self.page, s="div.F7nice > span:nth-child(1) > span.ceNzKf", m="aria-label")
        reviews = await self.extractor(p=self.page, s="div.F7nice > span:nth-child(2) > span > span", m="aria-label")
        location = await self.extractor(p=self.page, s="[data-item-id='address']", m="aria-label")
        website = await self.extractor(p=self.page, s='[data-item-id="authority"]', m="href")
        try:
            phone_ = await self.page.locator('[data-tooltip="Copy phone number"]').all()
            p = await phone_[0].get_attribute('aria-label')
            phone = p.split(":")[1]
        except:
            phone = "No phone number found"
        
        #Handle duplicate data
        if  name not in self.uniqueItem:                                                                                                          
            data = Resturants(
                Name=name, Stars=stars,
                Reviews=reviews, Location=location,
                Website=website, PhoneNumber=phone
            )
            log.info(data)
            save =  SaveData(file="extracted_data", folder=self.search)
            save.add_item(data)
            save.save_all()
            self.uniqueItem.append(name)
        else:
            log.info("Duplicate data Found and Handled")
            pass
             
    @timer         
    async def main(self):
        async with async_playwright() as self.playwright:
            await self.browser()
            await self.navigate()            
            await self.page.close()

if __name__ == '__main__':
    try:
        bot = GoogleBot("https://www.google.com/maps", "car park texas")
    except Exception as e:
        log.error(f'{e}', exc_info=True)

