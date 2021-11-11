# import everything from module
from module import *

# load the scraper object
sc = AirbnbScraper("https://www.airbnb.co.in/s/San-Francisco--CA--United-States/experiences")
print("program start")

# specify the initial variables
load_more_xpath = None
initial = True
count = 0

# loop the process to click load more
while True:
    xpath = '//*[@id="site-content"]'
    try:
        WebDriverWait(sc.browser,10).until(EC.element_to_be_clickable((By.XPATH,xpath)))
        load_more_xpath = sc.find_loadmore()
        links = sc.find_all_experiences()
        if initial:            
            old_len = len(links)
            initial = False
        else:
            if old_len == len(links):
                count += 1
                if count == 2:
                    print(": load more end")
                    break
            else:
                old_len = len(links)
                count = 0
        if load_more_xpath != None:
            sc.click_loadmore(load_more_xpath)
            time.sleep(1)
    except:
        break
        
print(":",len(links),"links retrieved\n")
        
# change the links into book
links = sc.change(links)

# scrape schedule data from the links
    
## get link
for link in links:

    print("visiting:",link)
    sc.browser.get(link)

    ## scroll down the page
    sc.auto_scroll()

    ## get all the data
    if sc.scrape_data:

        ### update available data
        sc.update_data()

        ### collect the schedule data
        sc.collect_data()

        ### save the data as JSON
        filename = "./output/AvailableDates.json"
        json.dump(sc.data,open(filename,"w"))