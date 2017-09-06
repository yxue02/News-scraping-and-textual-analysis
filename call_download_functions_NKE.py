import time
Counter = 0

ticker_list = ["NKE"]
search_list = ["NKE"]
year_start = 2001
year_end = 2014
import download_functions_quarter
print "Start Trial Number: " + str(Counter)
while Counter <20 and not download_functions_quarter.download_full_text(ticker_list, search_list, year_start, year_end):
    Counter +=1
    time.sleep(60)
    print "Start Trial Number: " + str(Counter)
    