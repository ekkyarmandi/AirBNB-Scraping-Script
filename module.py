# import necessary libraries
from bs4 import BeautifulSoup
import json
import time
import re
from datetime import datetime

# import selenium libraries
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# create a child webdriver object
class AirbnbScraper():
    
    def __init__(self,url):
        self.browser = webdriver.Chrome("./driver/chromedriver.exe")
        self.browser.get(url)
        self.classes = self.get_classes()
        self.main_divs = self.scrape_main_rows()
        self.get_n_results()
        self.scrolling_speed = 1 # sec
        self.data = json.load(open("./output/AvailableDates.json"))
        
    # get all classes list
    def get_classes(self):
        soups = BeautifulSoup(self.browser.page_source,"html.parser")
        soups = soups.find("body").find("style")
        style = re.findall("[._A-Za-z0-9]+",soups.string)
        classes = [name for name in style if name[0] == "."]
        classes = list(dict.fromkeys(classes))
        return classes
    
    # scrape the main page
    def scrape_main_rows(self):
        soups = BeautifulSoup(self.browser.page_source,"html.parser")
        all_rows = soups.find("main",{"id":"site-content"}).find_all("div",{"class":self.classes[3].strip(".")})
        all_rows = [row for row in all_rows if row.parent.name == "main"]
        return all_rows
    
    # get parameter from link
    def get_param(self,link):
        link_parameter = link.split("?")[-1].split("&")
        parameter = {}
        for param in link_parameter:
            var = param.split("=")[0]
            value = param.split("=")[-1]
            parameter.update({var:value})
        return parameter
    
    def find_all_experiences(self):        
        all_rows = self.scrape_main_rows()
        links = []
        for page in all_rows:    
            exps = page.find_all("a")
            for exp in exps:
                try:
                    link = "https://www.airbnb.co.in" + exp["href"]
                    if link.split("/")[3] == "experiences":
                        param = self.get_param(link)
                        if param['searchId'] == "":
                            links.append(link)
                except:
                    pass
        return links
    
    def change(self,links):
        new_links = []
        for link in links:
            code = link.split("?")[0].split("/")[-1]
            for j in range(1,7):
                new_link = "https://www.airbnb.co.in/experiences/{}?&modal=BOOK_IT&adults={}".format(code,j)
                new_links.append(new_link.format(code))
        return new_links
    
    def get_n_results(self):
        text = self.main_divs[0].text.strip()
        self.n_results = float(text.split(" ")[0])
    
    def find_loadmore(self):
        template = '//*[@id="site-content"]/div[{}]/div/div/div/div/div/div/button'
        load_more_xpath = None
        all_rows = self.scrape_main_rows()
        i = 0
        for page in all_rows:
            page_text = page.text.strip()
            if "load more" in page_text.lower():
                load_more_xpath = template.format(i+1)
                break
            i += 1
        return load_more_xpath
    
    def click_loadmore(self,xpath):
        try:
            WebDriverWait(self.browser,10).until(EC.element_to_be_clickable((By.XPATH,xpath)))
            element = self.browser.find_element_by_xpath(xpath)
            self.browser.execute_script("arguments[0].scrollIntoView();", element)
            self.browser.execute_script("window.scrollBy(0, -400);")
            element.click()
        except:
            pass
        
    def auto_scroll(self):        
        ### get window height from browser
        def get_window_height(driver):
            xpath = '/html/body/div[11]/section/div/div/div[2]/div/div/div'
            element = driver.find_element_by_xpath(xpath)
            return driver.execute_script("return arguments[0].scrollHeight", element)
        
        try:
            ### wait for the target element located
            xpath = '//*[@id="site-content"]/div/div/div/div/div/div[2]/div/div/div/section'
            WebDriverWait(self.browser,20).until(
                EC.presence_of_element_located((By.XPATH,xpath))
            )
            ### mimic human scroll down behavior
            old_height = get_window_height(self.browser)
            count = 0
            while True:
                #### scroll down
                xpath = '//*[@id="site-content"]/div/div/div/div/div/div[2]/div/div/div/section'
                self.browser.find_element_by_xpath(xpath).click() # select the current window
                self.browser.find_element_by_xpath('html').send_keys(Keys.END) # simlulate press END key on the current window
                time.sleep(self.scrolling_speed) # delay for 0.5 sec
                #### compare the height
                new_height = get_window_height(self.browser)
                if old_height != new_height:
                    old_height = new_height
                else:
                    count += 1
                    if count == 2:
                        break
            print("auto scroll: done")
            self.scrape_data = True
        except:
            print("auto scroll: internet fail")
            self.scrape_data = False
                    
    def update_data(self):
        
        def guest_text(parameter):
            n = parameter['adults']
            if n == "1":
                return "1 guest"
            else:                
                return n + " guests"
            
        parameter = self.get_param(self.browser.current_url)
        self.url_code = self.browser.current_url.split("?")[0].split("/")[-1]
        self.guest = guest_text(parameter)
        try:
            self.data['AvailableDates'][self.url_code].update({self.guest:[]})
        except:
            self.data['AvailableDates'].update({self.url_code:{self.guest:[]}})
        
    def collect_data(self):        
        def find_class(text):
            try:
                return text.parent.parent.parent.attrs['class'][0]
            except:
                return None
        ### get book page classes
        xpath = '//*[@id="site-content"]/div/div/div/div/div/div[2]/div/div/div/section/div/div/div/div/div/div[2]'
        class_name = self.browser.find_element_by_xpath(xpath).get_attribute("class")
        ### get schedule
        soups = BeautifulSoup(self.browser.page_source,"html.parser")
        soups = soups.find("div",{"class":class_name}).find("div")
        for line in soups.find_all("div"):
            div_class = find_class(line)
            if div_class == class_name:
                try:
                    date = datetime.strptime(line.text,"%a, %d %b")
                    date_schedule = line.text
                except:
                    time_schedule = line.find_next().find_all("div")[0]
                    time_schedule = time_schedule.next.next_element
                    schedule = date_schedule + " " + time_schedule
                    self.data['AvailableDates'][self.url_code][self.guest].append(schedule)