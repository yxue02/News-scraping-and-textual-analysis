import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException        
import unittest, time, re
import numpy as np

import requests
import bs4
from bs4 import BeautifulSoup
import math
from datetime import date, datetime, timedelta
import re
import pandas

#path_name = os.path.dirname(os.path.abspath(__file__))

def perdelta(start, end, delta):
    curr = start
    while curr < end:
        yield curr
        curr += delta
def fillInSource(sourceString, driver):
    # Fill in News Sources
    driver.find_element_by_id("scTxt").clear()
    driver.find_element_by_id("scTxt").send_keys(sourceString)
    driver.find_element_by_id("scLkp").click()
    time.sleep(3)
    driver.find_element_by_link_text(sourceString).click()
def downloadData(driver):
    # Download RTF files
    driver.find_element_by_css_selector("#selectAll > input:nth-child(1)").click()
    driver.find_element_by_xpath("//ul[@id='listMenuRoot']/li[5]/a").click()
    time.sleep(1)
    driver.find_element_by_xpath("(//a[contains(text(),'Article Format')])[3]").click()
    time.sleep(3)
def inputDate(date_start,date_end, driver):
    # Customize the start and end dates
    driver.find_element_by_id("frdt").clear()
    driver.find_element_by_id("frdt").send_keys(date_start)
    driver.find_element_by_id("todt").clear()
    driver.find_element_by_id("todt").send_keys(date_end)
    driver.find_element_by_id("btnSearchBottom").click()
    # wait for the page to load
    element = WebDriverWait(driver, 60).until(EC.invisibility_of_element_located((By.ID, "assistedSearchEditorControl")))
    time.sleep(1)

def modifySearch(driver):
    # Modify search
    driver.find_element_by_css_selector("#btnModifySearch > div:nth-child(1) > span:nth-child(1)").click()
    # wait for the page to load
    element = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "frdt")))
    time.sleep(1)

def check_clickable(element):
    try:
        element.click()
    except Exception:
        return False
    return True

def downloadText(ticker, year,quarter, filepath, driver):
    # Find total number of pages 
    num_obs = driver.find_element_by_css_selector("tr.even:nth-child(11) > td:nth-child(2)").text
    num_obs_clean = num_obs.encode('utf-8')
    num_obs = int(num_obs_clean.replace(',',''))
    num_pages = int(math.floor(num_obs/100))+1
    i = 0 
    # When there is still next 100
    while i < num_pages-1 and len(driver.find_elements_by_css_selector(".nextItem")) > 0:
        check_page_appearance(driver, year, quarter, i)
        if not os.path.isfile(os.path.join(filepath, "NewsInfo_"+ticker+"_"+str(year)+"_"+str(quarter)+"_"+str(i+1)+".csv")):
            getText(ticker, year,quarter, i, num_pages, filepath, driver)
            # Double check to make sure nextItem exists
        if len(driver.find_elements_by_css_selector(".nextItem")) > 0:
            element = WebDriverWait(driver, 100).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".nextItem")))
            time.sleep(10)
            driver.find_element_by_css_selector(".nextItem").click()
            time.sleep(10)
            i += 1 
    # Download last 100 items
    if not os.path.isfile(os.path.join(filepath, "NewsInfo_"+ticker+"_"+str(year)+"_"+str(quarter)+"_"+str(i+1)+".csv")):
        getText(ticker,year,quarter,i, num_pages, filepath, driver)

def click_and_download(element,ticker,indexes,dates,times,i, filepath, driver):
    element.click()
    WebDriverWait(driver,20).until(lambda driver: driver.find_elements(By.ID,"hd"))
    time.sleep(0.5)
    page_source = driver.page_source
    page_source_clean = page_source.encode('utf-8')
    soup = BeautifulSoup(page_source_clean,"lxml")
    paragraph_raw = soup.find_all('div',{ 'id' : "hldSplitterPane2"})
    for paragraph in paragraph_raw:
        paragraph_clean = paragraph.text.encode('utf8')
        paragraphs = re.split("\n+",paragraph_clean)
        text_file = open(os.path.join(filepath, "Output-" + ticker + '-' + str(indexes[i]) + '-' + str(dates[i])+'-'+ str(times[i]) + ".txt") , "w")
        find_start = 0
        write_index = []
        for paragraph in paragraphs:
            if paragraph.startswith('a certain string'):
                find_start = 1
            elif paragraph.startswith('another string'):
                find_start = 0
            else:
                if find_start ==1:
                    # print paragraph
                    text_file.write(paragraph)
                    text_file.write('\n')
        text_file.close()

def check_page_appearance(driver, year, quarter, j):
    index = driver.find_element_by_css_selector("#headlines > table:nth-child(1) > tbody:nth-child(1) > tr:nth-child(1) > td:nth-child(2)").text
    index1 = index.encode('utf-8')
    index2 = index1.replace('.','')
    index = int(index2.strip())
    counter = 1
    while index < j*100 +1 and counter<10:
        time.sleep(5)
        counter += 1 
        index = driver.find_element_by_css_selector("#headlines > table:nth-child(1) > tbody:nth-child(1) > tr:nth-child(1) > td:nth-child(2)").text
        index1 = index.encode('utf-8')
        index2 = index1.replace('.','')
        index = int(index2.strip())
    if index < j*100 +1:
        print "Something is wrong for year " + str(year) + " and quarter " + str(quarter) + " where index = " + str(index) + " while it should be " + str(j*100 +1)

# delete duplicates
def selectEffective(list_to_select,effective_index):
    return [list_to_select[i] for i in effective_index]

def getText(ticker, year,quarter,j,num_pages, filepath, driver):
    # Retrieve Text
    headlines = []
    dates = []
    times = []
    sources = []
    numWords = []
    indexes = []
    regex = r"\d+:\d+\s[AP]M"
    page_source = driver.page_source
    page_source_clean = page_source.encode('utf-8')
    soup = BeautifulSoup(page_source_clean,"lxml")
    # Get the raw text of headlines and leads (results are sets, check sequence)
    leads_raw = soup.find_all('div',{'class' : 'leadFields'})
    headlines_raw = soup.find_all('a',{'class': 'enHeadline'})
    indexes_raw = soup.find_all('td',{'class': 'count'})
    month_dict = {'January':1,'February':2, 'March':3, 'April':4, 'May':5, 'June':6, 'July':7, 'August':8, 'September':9, 'October':10, 'November':11, 'December':12}
    time_dict = {'AM':0, 'PM':1200}
    for headline_raw in headlines_raw:
        headline = headline_raw.text.encode('utf-8')
        headline = headline.replace("\n"," ")
        headlines.append(headline.strip())
    for index_raw in indexes_raw:
        index = index_raw.text.encode('utf-8')
        index_parts = index.split('.')
        indexes.append(index_parts[0].strip())
    indexes_effective = [0]
    for k in range(1,len(indexes)):
        if indexes[k] != indexes[k-1]:
            indexes_effective.append(k)
    for lead_raw in leads_raw:
        lead = lead_raw.text.encode('utf-8').strip()
        parts = lead.split(',')
        sources.append(parts[0].strip())
        if re.search(regex,parts[1].strip()):
            time_raw = parts[1].strip()
            time_parts = time_raw.split(' ')
            time_parts1 = time_parts[0].split(':')
            times.append(int(time_parts1[0])*100+int(time_parts1[1])+time_dict[time_parts[1]])
            date_parts = parts[2].strip().split()
            dates.append(int(date_parts[2])*10000 + month_dict[date_parts[1]]*100 + int(date_parts[0])) 
            num = parts[3].split(' ')
            numWords.append(num[1].strip())
        else:
            times.append("NA")
            date_parts = parts[1].strip().split()
            dates.append(int(date_parts[2])*10000 + month_dict[date_parts[1]]*100 + int(date_parts[0])) 
            num = parts[2].split(' ')
            numWords.append(num[1].strip())
    headlines = selectEffective(headlines, indexes_effective)
    indexes = selectEffective(indexes, indexes_effective)
    sources = selectEffective(sources, indexes_effective)
    # missing values
    news_info = []
    for i in range(0,len(headlines)):
        element = driver.find_element_by_css_selector("tr.headline:nth-child("+str(i+1)+") > td:nth-child(3) > a:nth-child(2)")
        if not element.is_displayed():
            element = driver.find_element_by_css_selector("#headlines > table:nth-child(1) > tbody:nth-child(1) > tr:nth-child("+str(i+1)+") > td:nth-child(3) > a:nth-child(2)")
        #if check_exists_by_css_selector("tr.headline:nth-child("+str(i+1)+") > td:nth-child(3) > a:nth-child(2)"):
        #    element = driver.find_element_by_css_selector("tr.headline:nth-child("+str(i+1)+") > td:nth-child(3) > a:nth-child(2)")
        #else:
        #    element = driver.find_element_by_css_selector("#headlines > table:nth-child(1) > tbody:nth-child(1) > tr:nth-child("+str(i+1)+") > td:nth-child(3) > a:nth-child(2)")
        element_class_attribute = element.get_attribute("onclick").encode('utf-8')
        if element_class_attribute[0:7] == 'article' and check_clickable(element):
            click_and_download(element,ticker,indexes,dates,times,i, filepath, driver)
            news_info.append([ticker,indexes[i],dates[i],times[i],headlines[i],sources[i],numWords[i],0])
        else: 
            news_info.append([ticker,indexes[i],dates[i],times[i],headlines[i],sources[i],numWords[i],1])
    # export news information
    columns = ["Ticker","Index","Date", "Time", "Headline", "Source", "NumWords", "missing"]
    ind = range(1,len(news_info)+1)
    data = news_info
    pd = pandas.DataFrame(data, columns = columns, index = ind)
    pd.to_csv(os.path.join(filepath, "NewsInfo_"+ticker+"_"+str(year)+"_"+str(quarter)+"_"+str(j+1)+".csv"))
    print "Progress: "+ str(j+1) + "/" + str(num_pages) + " for year " + str(year)  + " and quarter " + str(quarter) + " with ticker " + ticker  

def download_full_text(ticker_list, search_list, year_start, year_end):
    # Set firefox preferences
    fp = webdriver.FirefoxProfile()
    fp.set_preference("browser.download.folderList",2)
    fp.set_preference("browser.download.manager.showWhenStarting",False)
    driver = webdriver.Firefox(firefox_profile=fp)
    # driver = webdriver.Firefox()
    driver.get("a certain url")
    
        Select(driver.find_element_by_id("dr")).select_by_visible_text("Enter date range...")
        driver.find_element_by_id("frdt").clear()
        driver.find_element_by_id("frdt").send_keys("20010101")
        driver.find_element_by_id("todt").clear()
        driver.find_element_by_id("todt").send_keys("20010331")
        # Fill in News Sources
        sourceString_List = []
        for sourceString in sourceString_List:
            fillInSource(sourceString, driver)
        quarterList_Start = ['0101','0401','0701','1001']
        quarterList_End = ['0331','0630','0930','1231']
        #coTab > div:nth-child(1)
        #coTab > div:nth-child(1)
        #for j in range(0,len(ticker_list)):
        current_path = os.getcwd()
        flag = 0 # The first stock in the list
        for j in range(0,len(ticker_list)):
            ticker = ticker_list[j]
            # create new folder
            filepath = current_path + '/' + ticker
            if not os.path.exists(filepath):
                os.makedirs(filepath)
            if os.path.isfile(os.path.join(filepath, "All-finished-" + ticker  + ".txt")):
                        continue
            if flag == 0:
                driver.find_element_by_css_selector("#coTab > div.pnlTabArrow").click()
                flag = 1 # Already searched for a stock
            else:
                driver.find_element_by_css_selector("#coLst > div:nth-child(1) > ul:nth-child(1) > li:nth-child(1) > div:nth-child(1) > div:nth-child(1) > span:nth-child(1)").click()   
                driver.find_element_by_css_selector("div.pillOption:nth-child(2) > span:nth-child(1)").click()
            driver.find_element_by_id("coTxt").send_keys(search_list[j])
            time.sleep(3)
            driver.find_element_by_css_selector(".ac_descriptor > strong:nth-child(1)").click()
            # driver.find_element_by_css_selector("#coTab > div.pnlTabArrow").click()
            driver.find_element_by_id("btnSearchBottom").click()
            time.sleep(8)

            # Download data by year
            for year in range(year_start,year_end+1):
                for quarter in range(1,5):
                    if os.path.isfile(os.path.join(filepath, "Finished-" + ticker + '-'+ str(year) + '-' + str(quarter) + '-' + ".txt")):
                        continue
                    modifySearch(driver)
                    inputDate(str(year)+quarterList_Start[quarter-1],str(year)+quarterList_End[quarter-1],driver)
                    downloadText(ticker, year,quarter, filepath, driver)
                    text_file = open(os.path.join(filepath, "Finished-" + ticker + '-' + str(year) + '-' + str(quarter) + '-' + ".txt") , "w")
                    text_file.write('Hello World!')
                    text_file.close()
            modifySearch(driver)
            text_file = open(os.path.join(filepath, "All-finished-" + ticker  + ".txt") , "w")
            text_file.write('Hello World!')
            text_file.close()
        return True
    except Exception as e:
        try:
            print str(e).encode('utf-8')
        except Exception as e2:
            print "This ugly alert occurs again!"
        #try:
        #    driver.close()
        #except Exception as e3:
        #    print "Unable to close driver"

        return False

