from string import digits
from pathlib import Path
import sys
from PIL import Image, ImageOps
from urllib.request import urlopen
import urllib.request
from bs4 import BeautifulSoup
import re
import os, shutil
from os import path
from PyPDF2 import PdfMerger

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

saved_cards = []

def check_saved_card_exists(cardname):
    global saved_cards
    if len(saved_cards) == 0:
        saved_cards = [x.strip() for x in open("saved_cards.txt",'r').readlines()]

    for card in saved_cards:
        saved_card_name = card.split(';')[0]
        saved_card_file = card.split(';')[1]
        if saved_card_name == cardname:
           return saved_card_file 
    return None

def save_card_to_cache(card_name,image_file_name):
    append_new_line("saved_cards.txt", card_name+";"+image_file_name)
    

def main(*args):
    # make sure saved / cached cards file exists
    Path('saved_cards.txt').touch()

    # get each arg (a decklist)
    if len(sys.argv) <= 1:
        print('\n'+bcolors.WARNING+" no arg supplied"+bcolors.ENDC)
        print('\n'+bcolors.OKBLUE+"usage: "+bcolors.ENDC+"python print.py file1.txt file2.txt\n each file should be a Magic the Gathering decklist.\n\n "+bcolors.UNDERLINE+"Sample_file.txt"+bcolors.ENDC+bcolors.OKCYAN+"\n 1 Ant Queen \n 4 Sword of Fire and Ice \n 2 Rite of Replication"+bcolors.ENDC+"\n")
    for arg in sys.argv[1:]:
        print("arg:"+arg)
    for filename in sys.argv[1:]:
        # for each decklist,
        master_list = {}    

        cards = [x.strip() for x in open(filename,'r').readlines()]
        
        # for each card in that decklist,
        for card in cards:
            if len(card) == 0 or not card[0].isnumeric() or len(card.split(' ')[0]) != 1:
                print(bcolors.WARNING+"SKIP "+bcolors.ENDC+"card, no num")
                continue
                        
            # separate number from search, e.g. "4 Angel of Avacyn" becomes "Angel of Avacyn"
            count, card_name, card_name_lower = int(card[:1]), card[2:], card[2:].lower()

            if card_name_lower == "swamp" or card_name_lower == "island" or card_name_lower =="mountain" or card_name_lower =="forest" or card_name_lower == "plains":
                print(bcolors.WARNING+"LAND SKIPPED"+bcolors.ENDC+": "+card_name)
                continue

            # Did we already download this card before?
            saved_card_file_name = check_saved_card_exists(card_name)
            image_file_name = None

            # if so, read the file name from the saved_cards.txt and don't bother downloading it
            if saved_card_file_name is not None: 
                sys.stdout.write(bcolors.OKBLUE+'card '+card_name+' was saved! ('+saved_card_file_name+') -- skip check')
                print(bcolors.ENDC)
                image_file_name = saved_card_file_name
                master_list['images/'+image_file_name] = count
            
            # Nope I've never seen this card before in my life. Download it
            else:
                # use scryfall opensearch from opensearch.xml on scryfall.com source
                url = 'https://scryfall.com/search?as=grid&order=name&q='+card_name.replace(' ','+')+'+%28game%3Apaper%29'
                print("Searching:"+url);
                html = urlopen(url)
                bs = BeautifulSoup(html,'html.parser')

                # here, it's possible we found multiple cards.
                # if so, the first one is usually correct (shortest name).
                if bs.find_all("a", {"class": "card-grid-item-card"}):
                    print(bcolors.OKBLUE+'name '+str(card)+' returned multiple results; picking first')
                    print(bcolors.ENDC)
                    card_link = bs.find_all("a", {"class": "card-grid-item-card"})[0]['href']
                    html = urlopen(card_link)
                    bs = BeautifulSoup(html,'html.parser')
                
                image_file_name = get_and_save_image(bs,0)
   
                # Finally - was this a Transform card with a back? If so, 
                if len(bs.find_all('div', {"class":"card-image-back"})) != 0:
                    print("~~~ HAS BACK!")
                    # it was a wacky Transform card. First add the front that we already got.
                    master_list['images/'+image_file_name] = count
                
                    image_back_file_name = get_and_save_image(bs,1)
                    master_list['images/'+image_back_file_name] = count
                    # DO NOT save cards with backs, just look it up each time.. easier
                    

                else:
                    # We downloaded a card. 
                    # it wasn't a fancy transform card with a back.
                    # Now save the card! For later. :-]
                    save_card_to_cache(card_name,image_file_name)
                    master_list['images/'+image_file_name] = count

            # Now, we have the card image
            # but sometimes card image is wrong size
            # let's make sure its right size, 672x936

#            im = Image.open('images/'+image_file_name)
#            im = im.resize((672, 936))
#            im.save('images/'+image_file_name)

        
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

        merger = PdfMerger()

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
#    print('\n combine starting with:\n'+str(image_files)+'\n')
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

    # pad the outside to make cards smaller / easier to sleeve
    new_im = ImageOps.expand(new_im,border=25,fill='black')
    new_im = ImageOps.expand(new_im,border=25,fill='white')

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

def append_new_line(file_name, text_to_append):
    """Append given text as a new line at the end of file"""
    # Open the file in append & read mode ('a+')
    with open(file_name, "a+") as file_object:
        # Move read cursor to the start of file.
        file_object.seek(0)
        # If file is not empty then append '\n'
        data = file_object.read(100)
        if len(data) > 0:
            file_object.write("\n")
        # Append text at the end of file
        file_object.write(text_to_append)

def get_and_save_image(bs,index):
    image_url = bs.find_all('img')[index]['src']
    image_file_name = re.search('([^\/]+$)',image_url)[0] # after last "/"
    image_file_name = re.search('([^?]*)', image_file_name)[0] # before "?"
    print(bcolors.OKBLUE+'adding:'+image_file_name)
    if index != 1: image_file_name = "back_"+image_file_name
    urllib.request.urlretrieve(image_url,'images/'+image_file_name)
    return image_file_name



if __name__ == "__main__":
    # execute only if run as a script
    main()

