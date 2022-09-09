# ===============================================================================
# =========================== IMPORTING LIBRARIES ===============================
# ===============================================================================

import os
import sys
import math
import heapq
import xml.sax
from datetime import datetime
from preprocess import Preprocess
from collections import defaultdict

# ===============================================================================
# ============================ GLOBAL VARIABLES =================================
# ===============================================================================

start_time = 0
abs_xml_path = ""
abs_index_path = ""
stat_file = ""

# CAPPING
TITLE_FILE_CAP = 200000 # 200 K (2 lacs)
MAX_TEMP_INDEX_CAP = 500000000 #  500 MB TEMP file size
MAX_INDEX_FILE_CAP = 1000000 # 1 MB Final Index file size

# STATISTICS
TotalDocCount = 0
TotalWordsEncountered = 0
TotalWords = 0
TotalUniqueWords = 0

# ===============================================================================
# ============================ WIKI HANDLER CLASS ===============================
# ===============================================================================

class WikiHandler(xml.sax.ContentHandler):
    # initialize the class
    def __init__(self):
        self.docID = 0
        self.page_data = {}
        self.allowed_tags = ["title", "text"]
        self.current_tag = ""
        self.wiki_data = {}
        self.field = ["title", "body", "infobox", "category", "link", "ref"]
        # preprocessing
        self.PP = Preprocess()
        # inverted index
        self.inverted_index = {}
        self.inverted_index_size = 0
        self.MAX_TEMP_INDEX_CAP = MAX_TEMP_INDEX_CAP

    def startElement(self, tag, attrs):
        self.current_tag = tag
        if tag == "page":
            self.page_data = {}
            for tag in self.allowed_tags:
                self.page_data[tag] = ""
            self.wiki_data = {}
            for f in self.field:
                self.wiki_data[f] = ""
            
    def endElement(self, tag):
        if(tag == "page"):
            self.docID += 1 # moved forward instead of end to simplify offline title writing

            # logs
            if(self.docID % 10000 == 0):
                print("Documents Indexed: ", self.docID)

            # update total_doc count for the dump
            global TotalDocCount
            TotalDocCount = self.docID + 1 # bc 0 based indexing

            if len(self.page_data["title"]) > 0 and len(self.page_data["text"]) > 0:
                self.wiki_data["title"] = self.PP.process_title(self.page_data["title"])
                self.wiki_data["infobox"], self.wiki_data["body"], self.wiki_data["category"], self.wiki_data["link"], self.wiki_data["ref"] = self.PP.process_text(self.page_data["text"])
                
            
            # update total_words_encountered for the dump
            global TotalWordsEncountered
            TotalWordsEncountered = self.PP.TotalWordsEncountered


            # maintain a global title list using page_data["title"]
            add_title_offline(self.docID, self.page_data["title"].replace("\n", " "))

            self.build_inverted_index()

            # inverted index size contains how many words in have been encountered so far
            # in the documents parsed. This can be a representative of how large the
            # inverted index is. Also can be used as a metric to cutoff the online inverted
            # index building process and save the current inverted index to disk.
            if(self.inverted_index_size > self.MAX_TEMP_INDEX_CAP):
                create_offline_temp_index(self.inverted_index)
                self.inverted_index = {}
                self.inverted_index_size = 0

            # post processing(cleaning)
            self.current_tag = ""
            self.page_data = {}
            self.wiki_data = {}

        # to handle the last chunk of the inverted index
        if tag == "mediawiki" and self.inverted_index_size > 0:
            create_offline_temp_index(self.inverted_index)
            self.inverted_index = {}
            self.inverted_index_size = 0


    def characters(self, content):
        if self.current_tag in self.allowed_tags:
            self.page_data[self.current_tag] += content.strip()

    # ============================= INVERTED INDEX ==================================

    def build_inverted_index(self):
        title = self.wiki_data["title"]
        infobox = self.wiki_data["infobox"]
        body = self.wiki_data["body"]
        category = self.wiki_data["category"]
        link = self.wiki_data["link"]
        ref = self.wiki_data["ref"]
        
        combined_words = defaultdict(int)

        # title
        title_dict = defaultdict(int)
        for word in title:
            title_dict[word] += 1
            combined_words[word] += 1
        
        # infobox
        infobox_dict = defaultdict(int)
        for word in infobox:
            infobox_dict[word] += 1
            combined_words[word] += 1

        # body
        body_dict = defaultdict(int)
        for word in body:
            body_dict[word] += 1
            combined_words[word] += 1

        # category
        category_dict = defaultdict(int)
        for word in category:
            category_dict[word] += 1
            combined_words[word] += 1

        # link
        link_dict = defaultdict(int)
        for word in link:
            link_dict[word] += 1
            combined_words[word] += 1

        # ref
        ref_dict = defaultdict(int)
        for word in ref:
            ref_dict[word] += 1
            combined_words[word] += 1

        for word, word_count_in_doc in combined_words.items():
            index_string = str(self.docID) + " "
            if(title_dict[word] > 0):
                index_string += "t" + str(title_dict[word])
            if(infobox_dict[word] > 0):
                index_string += "i" + str(infobox_dict[word])
            if(body_dict[word] > 0):
                index_string += "b" + str(body_dict[word])
            if(category_dict[word] > 0):
                index_string += "c" + str(category_dict[word])
            if(link_dict[word] > 0):
                index_string += "l" + str(link_dict[word])
            if(ref_dict[word] > 0):
                index_string += "r" + str(ref_dict[word])

            # merge into inverted_index
            if(word not in self.inverted_index):
                self.inverted_index[word] = {"doc_count":0, "total_count": 0, "posting_list": []}
            self.inverted_index[word]["doc_count"] += 1
            self.inverted_index[word]["total_count"] += word_count_in_doc
            self.inverted_index[word]["posting_list"].append(index_string)
            self.inverted_index_size += len(index_string)

# ===============================================================================
# ========================== WRITE TITLE OFFLINE ================================
# ===============================================================================

title_fp = None
title_file_count = 0

def add_title_offline(docID, title):
    global title_fp, title_file_count, abs_index_path
    if(docID % TITLE_FILE_CAP == 0 and docID > 0):
        title_file_count += 1
        title_fp.close()
        title_fname = "title_" + str(title_file_count) + ".txt"
        title_fp = open(os.path.join(abs_index_path, title_fname), "w")
    title_fp.write(title + "\n")

# ===============================================================================
# ======================== CREATE TEMP OFFLINE INDEX ============================
# ===============================================================================

temp_index_idx = 0

def create_offline_temp_index(inverted_index):
    global temp_index_idx, abs_index_path
    fname = "temp_index_" + str(temp_index_idx) + ".txt"
    with open(os.path.join(abs_index_path, fname), "w") as temp_index_fp:
        for word in sorted(inverted_index.keys()):
            posting_list = inverted_index[word]
            temp_index_fp.write(word + "=" + str(posting_list["doc_count"]) + "=" + str(posting_list["total_count"]) + "=" + "|".join(posting_list["posting_list"]) + "\n")
    temp_index_fp.close()
    temp_index_idx += 1


# ===============================================================================
# ======================== CREATE FINAL OFFLINE INDEX ===========================
# ===============================================================================

final_index_size = 0
final_index_count = 0
final_index_fp = None

def get_IDF(doc_count):
    return math.log10(TotalDocCount / doc_count)

def create_final_offline_index(final_inverted_index):
    global final_index_size, final_index_fp, final_index_count, abs_index_path
    if(final_index_size > MAX_INDEX_FILE_CAP):
        final_index_count += 1
        final_index_fp.close()
        final_index_size = 0
        index_fname = "index_" + str(final_index_count) + ".txt"
        final_index_fp = open(os.path.join(abs_index_path, index_fname), "w")
    
    final_inverted_index["IDF"] = get_IDF(final_inverted_index["doc_count"])
    line = final_inverted_index["word"] + "=" + str(final_inverted_index["IDF"]) + "=" + str(final_inverted_index["doc_count"]) + "=" + str(final_inverted_index["total_count"]) + "=" + final_inverted_index["posting_list"]
    final_index_fp.write(line + "\n")
    final_index_size += len(line)

    global TotalUniqueWords, TotalWords
    TotalUniqueWords += 1
    TotalWords += final_inverted_index["total_count"]


# ===============================================================================
# =========================== MERGE TEMP INDEXES ================================
# ===============================================================================

def merge_temp_indexes():
    global abs_index_path, final_index_fp

    # create an empty index file
    index_fname = "index_" + str(final_index_count) + ".txt"
    final_index_fp = open(os.path.join(abs_index_path, index_fname), "w")

    temp_fp_list = []
    inverted_index = {} # contains inverted index for one word of each doc
    min_heap = []
    final_inverted_index = {"word": "", "doc_count": 0, "word_freq": 0, "IDF": 0.0, "posting_list": ""} # contains the final inverted index of a word
    temp_file_count = temp_index_idx
    for idx in range(temp_file_count):
        fname = "temp_index_" + str(idx) + ".txt"
        temp_fp_list.append(open(os.path.join(abs_index_path, fname), "r"))
        line = temp_fp_list[idx].readline().strip("\n")
        if(line != ""):
            word, doc_count, word_freq, posting_list = line.split("=")
            min_heap.append((word, idx))
            # heapq.heappush(min_heap, (word, idx))
            inverted_index[idx] = {"doc_count": int(doc_count), "total_count": int(word_freq), "posting_list": posting_list}

    heapq.heapify(min_heap)

    while(len(min_heap) > 0):
        word, idx = heapq.heappop(min_heap)
        if(word == final_inverted_index["word"]):
            final_inverted_index["doc_count"] += inverted_index[idx]["doc_count"]
            final_inverted_index["total_count"] += inverted_index[idx]["total_count"]
            final_inverted_index["posting_list"] += "|" + inverted_index[idx]["posting_list"]
        else:
            if(final_inverted_index["word"] != ""):
                create_final_offline_index(final_inverted_index)
            final_inverted_index["word"] = word
            final_inverted_index["doc_count"] = inverted_index[idx]["doc_count"]
            final_inverted_index["total_count"] = inverted_index[idx]["total_count"]
            final_inverted_index["posting_list"] = inverted_index[idx]["posting_list"]
            
        line = temp_fp_list[idx].readline().strip("\n")
        if(line != ""):
            word, doc_count, word_freq, posting_list = line.split("=")
            heapq.heappush(min_heap, (word, idx))
            inverted_index[idx] = {"doc_count": int(doc_count), "total_count": int(word_freq), "posting_list": posting_list}
        else:
            temp_fp_list[idx].close()
            temp_file_count -= 1
            if temp_file_count == 0:
                break
        
    # close the final index file
    final_index_fp.close()
    

# ===============================================================================
# =========================== PURGE EXISTING INDEX ==============================
# ===============================================================================

def purge_temp_index():
    for f in os.listdir(abs_index_path):
        if f.startswith("temp_index_"):
            os.remove(os.path.join(abs_index_path, f))

def purge_existing_index():
    # purge temp files
    purge_temp_index()

    for f in os.listdir(abs_index_path):
        # purge title and files in abs_path_idx
        if(f.startswith("title_") or f.startswith("index_")):
            os.remove(os.path.join(abs_index_path, f))
        # purge_secondary_index
        if(f.startswith("secondary_index")):
            os.remove(os.path.join(abs_index_path, f))
    

# ===============================================================================
# ========================== PRIMARY INDEX CREATION =============================
# ===============================================================================

def create_primary_index():
    # purge the existing primary index
    purge_existing_index()

    # open title file
    global title_fp
    title_fname = "title_" + str(title_file_count) + ".txt"
    title_fp = open(os.path.join(abs_index_path, title_fname), "w")

    # create a WikiHandler object
    handler = WikiHandler()
    # create a parser
    parser = xml.sax.make_parser()
    # turn off namepsaces
    parser.setFeature(xml.sax.handler.feature_namespaces, 0)
    # connect parser to the handler
    parser.setContentHandler(handler)
    # parse the file
    parser.parse(abs_xml_path)

    #close title file
    title_fp.close()

    global start_time
    print("\n================================================\n")
    temp_file_creation_time = datetime.utcnow()
    print("Temp Indexes Created in %s seconds" % (temp_file_creation_time - start_time).total_seconds())
    print("\n================================================\n")

    # merge the temp indexes
    merge_temp_indexes()
    print("\n================================================\n")
    merge_file_time = datetime.utcnow()
    print("Merged Temp Indexes in %s seconds" % (merge_file_time - temp_file_creation_time).total_seconds())
    print("\n================================================\n")

    #purge the temp indexes
    purge_temp_index()


# ===============================================================================
# ========================= SECONDARY INDEX CREATION ============================
# ===============================================================================

def create_secondary_index():
    first_word_file = []
    for f in os.listdir(abs_index_path):
        if f.startswith("index_"):
            fp = open(os.path.join(abs_index_path, f), "r")
            line = fp.readline().strip("\n").split("=")
            if(len(line) > 0):
                first_word_file.append(line[0])
            fp.close()
    # because files are picked up in a random order, sort the list
    first_word_file.sort()

    secondary_fname = "secondary_index.txt"
    secondary_fp = open(os.path.join(abs_index_path, secondary_fname), "w")
    for word in first_word_file:
        secondary_fp.write(word + "\n")
    secondary_fp.close()
    

# ===============================================================================
# ============================== WRITE STAT FILE ================================
# ===============================================================================

def get_index_size():
    size = 0
    for path, dirs, files in os.walk(abs_index_path):
        for f in files:
            fp = os.path.join(path, f)
            size += os.path.getsize(fp)
    return size

def generate_statistics(primary_index_time, secondary_index_time):
    global stat_file
    stat_fp = open(stat_file, "w")
    stat_fp.write("Total Documents: \t\t\t\t" + str(TotalDocCount) + "\n")
    stat_fp.write("Total Tokens Encountered: \t\t" + str(TotalWordsEncountered) + "\n")
    stat_fp.write("Total Tokens Indexed: \t\t\t" + str(TotalWords) + "\n")
    stat_fp.write("Total Unique Tokens: \t\t\t" + str(TotalUniqueWords) + "\n")
    sz = get_index_size()
    sz = sz / (1024 * 1024)
    stat_fp.write("Index Size: \t\t\t\t\t%.2f MB\n" % sz)
    # adding +1 because title_file_count and final_file_count are 0 based indexed
    stat_fp.write("Title File Count: \t\t\t\t" + str(title_file_count+1) + "\n")
    stat_fp.write("Primary Index File count: \t\t" + str(final_index_count+1) + "\n")
    stat_fp.write("Secondary Index File count: \t" + str(1) + "\n")
    stat_fp.write("Primary Index Creation Time: \t%.2f seconds\n" % primary_index_time)
    stat_fp.write("Secondary Index Creation Time: \t%.2f seconds" % secondary_index_time)
    stat_fp.close()

# ===============================================================================
# ================================== MAIN =======================================
# ===============================================================================

def main():
    if(len(sys.argv) != 4):
        print("Invalid number of arguments")
        print("Expected 3 arguments: <path_to_xml_dump> <path_to_index_folder> <stat_file_name>")
        exit(1)

    global start_time, abs_xml_path, abs_index_path, stat_file

    start_time = datetime.utcnow()
    abs_xml_path = os.path.abspath(sys.argv[1])
    abs_index_path = os.path.abspath(sys.argv[2])
    stat_file = sys.argv[3]

    if(not os.path.isfile(abs_xml_path)):
        print("Invalid xml file path")
        exit(1)
    
    if(not os.path.isdir(abs_index_path)):
        print("Invalid index folder path, creating index folder '", sys.argv[2], "'", sep='')
        os.mkdir(abs_index_path)

    # ===============================================================================

    create_primary_index()
    primary_end_time = datetime.utcnow()
    primary_index_time = (primary_end_time - start_time).total_seconds()
    print("Primary Index creation time:", primary_index_time, "seconds")

    create_secondary_index()
    secondary_end_time = datetime.utcnow()
    secondary_index_time = (secondary_end_time - primary_end_time).total_seconds()
    print("Secondary Index creation time:", secondary_index_time, "seconds")

    generate_statistics(primary_index_time, secondary_index_time)

    # ===============================================================================
    
    return

if __name__ == "__main__":
    main()