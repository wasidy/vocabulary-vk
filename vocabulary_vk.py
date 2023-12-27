# -*- coding: utf-8 -*-
"""

Created on Mon Dec 25 21:44:44 2023

@author: Vasiliy Stepanov
"""

import os
from sys import argv
from bs4 import BeautifulSoup
import re
import time
import spacy
import json

def scan_files(base_path, extention):

    file_list = [os.path.join(root, name) for root, folder, files in os.walk(base_path) \
                 for name in files if name.endswith(extention)]
    return file_list


# Testing manual parsing of html from VK (because structure is simple)
# Faster 30x times comparing BeautifulSoup
def extract_manual_parsing(files, target_file):

    with open(target_file, 'w', encoding='utf-8') as targetfile:

        for x, f in enumerate(files):
            with open(f) as fp:
                html_code = fp.readlines()
            
            html_iter = iter(html_code)

            while html_iter:
                try:
                    html_string = next(html_iter)
                    if html_string[0:34] == '  <div class="message__header">Вы,':
                        try:
                            message_text = next(html_iter)
                            if len(message_text)>1:
                                cleaned_text = re.sub('\s+', ' ',
                                                      re.sub(u'\W|[0-9]|[a-zA-Z]',
                                                             ' ', message_text)).strip()
                                if cleaned_text:
                                    print (cleaned_text, file=targetfile)

                        except:
                            break
                except:
                    break
    return None


# Very slow. Obsolete
def extract_my_messages(files, target_file):

    with open(target_file, 'w', encoding='utf-8') as targetfile:
        for x, f in enumerate(files):
            with open(f) as fp:

                soup = BeautifulSoup(fp, 'html.parser')
                for div in soup.find_all('div', {'class': 'message'}):
                    
                    if div.text[1:4] == 'Вы,':
                        message_text= div.text.split('\n')[2]
                        
                        if len(message_text)>1:
                            cleaned_text = re.sub('\s+', ' ', re.sub(u'\W|[0-9]|[a-zA-Z]', ' ', message_text)).strip()
                            if cleaned_text:
                                print (cleaned_text, file=targetfile)
    return None


def lemmatize(file, max_block = 4096, max_chr = 100000000, target_json_file = ""):
    spacy.prefer_gpu()
    nlp = spacy.load("ru_core_news_lg", disable = ['parser','ner'])
    dictionary = {}
    total_tokens = 0
    uniq_tokens = 0
    
    with open(file, encoding='utf-8') as f:
        
        processed_text = f.read()
        processed_text_size = len(processed_text)
        
        max_chr = processed_text_size if max_chr > processed_text_size else max_chr
        max_block = max_chr if max_block > max_chr else max_block
            
        pos = 0
        
        while pos < max_chr:
            if max_block >= max_chr-pos:
                text_block = processed_text[pos:max_chr]
                pos = max_chr
            else:
                for j in range (pos+max_block, pos, -1):
                    current_chr = processed_text[j]
                    if current_chr == ' ' or current_chr == '\n':
                        text_block = processed_text[pos-1:j]
                        pos = j + 1
                        break
                    
            text = ' '.join(text_block.split())
            
            doc = nlp(text.lower())
            
            for token in doc:
                total_tokens += 1
                if not dictionary.get(token.lemma_):
                    dictionary[token.lemma_] = 1
                    uniq_tokens += 1
                else:
                    dictionary[token.lemma_] = dictionary[token.lemma_] + 1
            print (f'Tokens processed:{total_tokens}, unique:{uniq_tokens}')
        
        with open(target_json_file, 'w', encoding='utf-8') as f2:
            json.dump(dictionary, f2, ensure_ascii=False, indent=4)
            
    return None


def sort_and_save(file, filetosave):
    with open(file, encoding='utf-8') as f:
        dictionary  = json.load(f)
        
    sorted_dict = dict(sorted(dictionary.items(), key = lambda x: x[1], reverse = True))

    with open(filetosave, 'w', encoding='utf-8') as f2:
        json.dump(sorted_dict, f2, ensure_ascii=False, indent=4)
        
    return None


if __name__ == '__main__':
    
    #script, source_folder, subfolders = argv
    source_folder = 'C:\\Scripts\\VK_text_statistics'
    subfolders = True
    raw_text_file = 'C:\\Scripts\\VK_text_statistics\\messages.txt'
    dict_file = 'C:\\Scripts\\VK_text_statistics\\dic_unsorted.txt'
    sorted_dict = 'C:\\Scripts\\VK_text_statistics\\dic_sorted.txt'
    
    if not os.path.exists(raw_text_file):
    
        start_time = time.time()
        files = scan_files(source_folder, '.html')
        print ("Scan files in subfolders, time (s):", time.time()-start_time)
        
        start_time = time.time()
        extract_manual_parsing(files, raw_text_file)
        print ("Parsing using iterator, time (s):", time.time()-start_time)
    
    if not os.path.exists(dict_file):
                
        print ("File found, processing...")
        lemmatize(raw_text_file, target_json_file=dict_file)
    
    sort_and_save(dict_file, sorted_dict)
    
    print ("Done!")
    
    pass
