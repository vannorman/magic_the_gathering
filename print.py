import sys
from PIL import Image, ImageOps
from urllib.request import urlopen
import urllib.request
from bs4 import BeautifulSoup
import re
import os, shutil
from os import path
from PyPDF2 import PdfFileMerger

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    NORMAL = '\033[00m'

def main(*args):
    if len(sys.argv) <= 1:
        print('\n'+bcolors.WARNING+" no arg supplied"+bcolors.ENDC)
        print('\n'+bcolors.OKBLUE+"usage: "+bcolors.ENDC+"python print.py file1.txt file2.txt\n each file should be a Magic the Gathering decklist.\n\n "+bcolors.UNDERLINE+"Sample_file.txt"+bcolors.ENDC+bcolors.OKCYAN+"\n 1 Ant Queen \n 4 Sword of Fire and Ice \n 2 Rite of Replication"+bcolors.ENDC+"\n")
    for arg in sys.argv[1:]:
        print("arg:"+arg)
    for filename in sys.argv[1:]:
        master_list = {}    

        cards = [x.strip() for x in open(filename,'r').readlines()]
        for card in cards:
            if len(card) == 0 or not card[0].isnumeric():
                print(bcolors.WARNING+"SKIP "+bcolors.ENDC+"card, no num")
                continue
            # separate number from search
            count, search_term = int(card[:1]), card[2:]
        
            # use scryfall opensearch from opensearch.xml on scryfall.com source
            html = urlopen('https://scryfall.com/search?q='+search_term.replace(' ',''))
    #       print(str(html)[:40])
            bs = BeautifulSoup(html,'html.parser')
            image_url = bs.find_all('img')[0]['src']
            image_file_name = re.search('([^\/]+$)',image_url)[0] # after last "/"
            image_file_name = re.search('([^?]*)', image_file_name)[0] # before "?"
            if path.exists('images/'+image_file_name):
                print(bcolors.OKCYAN+'image '+image_file_name+' exists, skipping!')
            else:
                print(bcolors.OKBLUE+'adding:'+image_file_name)
                urllib.request.urlretrieve(image_url,'images/'+image_file_name)

            print(bcolors.ENDC)
            master_list['images/'+image_file_name] = count
        
        print(master_list)
        # expand master list to file list, with duplicates for count
        cards_to_print = []
        for item in master_list:
            for x in range(master_list[item]):
                cards_to_print.append(item)

        print(bcolors.BOLD+'cards ready!'+bcolors.ENDC)
        print('card count:'+str(len(cards_to_print)))
        print('\n')

        # take each 9 and make a file. Keep track of files
        count = 0
        batch = []
        pages = []
        for card in cards_to_print:
            batch.append(card)
            count += 1
            if count % 9 == 0: # take each 9 cards then make a page
                page = combine(batch)
                pages.append(page)
                batch = []
            elif count == len(cards_to_print): # last element
                page = combine(batch)
                pages.append(page)
                

        print('finished pages. count:'+str(len(pages)))
        page_files = []
        count = 0
        for page in pages:
            count += 1
            page_name = 'page_'+str(count)+'.pdf'
            page.save("temp/"+page_name)
            page_files.append("temp/"+page_name)

        merger = PdfFileMerger()

        for pdf in page_files:
            merger.append(pdf)

        filename = re.search('[^\.]+',filename)[0] #strip the .txt
        merger.write("output/"+filename+"_final.pdf")
        merger.close()
        print(bcolors.OKBLUE+"finished:"+bcolors.ENDC+" "+filename)

        #cleanup
#        for page in pages:
#            page_name = 'page_'+str(count)+'.pdf'
#            os.remove(page_name)

    clean_temp_dir() 



    
        
def combine(image_files = ['a.png' for i in range(9)]):
    # print('\n combine starting with:\n'+str(image_files)+'\n')
    images = [Image.open(x) for x in image_files]

    c1 = 9 # crop border size
    images = [x.crop((c1,c1,x.size[0]-(c1*2),x.size[1]-(c1*2))) for x in images]
    # add black border of same size
    images = [ImageOps.expand(x,border=9,fill='black') for x in images]
    
    images = [ImageOps.expand(x,border=1,fill='#444') for x in images]
    
    total_width = images[0].size[0] * 3
    total_height = images[0].size[1] * 3

    new_im = Image.new('RGB', (total_width, total_height), color="#fff")

    x_offset = 0
    y_offset = 0
    count = 0
    for im in images:
        count += 1
        new_im.paste(im, (x_offset,y_offset))
        if count % 3 == 0:  
            x_offset = 0
            y_offset += im.size[1]
        else:   
            x_offset += im.size[0]
    return new_im

def clean_temp_dir():
    folder = 'temp'
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

if __name__ == "__main__":
    # execute only if run as a script
    main()


