from curses.panel import top_panel
import os
import sys
from nltk.corpus import stopwords
from nltk import word_tokenize
from nltk import PorterStemmer
from datetime import datetime
from collections import defaultdict
import heapq


# section_weight = {"t": 1, "i": 1, "b": 1, "c": 1, "l": 1, "r": 1}
section_weight = [1000.0, 650.0, 50.0, 150.0, 200.0, 175.0]
title_per_file = 1000
K = 10 #top K documents to be returned

abs_index_path = ""
query_in = ""
interactive = False
query_in_file = ""
query_in_string = ""
field_identifier = {"t:", "i:", "b:", "c:", "l:", "r:"}
is_field_query = False
stopwords = set(stopwords.words('english'))
stemmer = PorterStemmer()
secondary_index = []

def get_index_file_idx(word):
    global secondary_index
    for idx, entry in enumerate(secondary_index):
        if(word < entry):
            return idx - 1
    return len(secondary_index) - 1

def extract_field_count(str):
    fields = [0, 0, 0, 0, 0, 0]
    for i in range(0, len(str)):
        if str[i] == "t":
            j = i+1
            while(j < len(str) and str[j] <= "9" and str[j] >= "0"):
                j += 1
            fields[0] = int(str[i+1:j])
            i = j
        elif str[i] == "i":
            j = i+1
            while(j < len(str) and str[j] <= "9" and str[j] >= "0"):
                j += 1
            fields[1] = int(str[i+1:j])
            i = j
        elif str[i] == "b":
            j = i+1
            while(j < len(str) and str[j] <= "9" and str[j] >= "0"):
                j += 1
            fields[2] = int(str[i+1:j])
            i = j
        elif str[i] == "c":
            j = i+1
            while(j < len(str) and str[j] <= "9" and str[j] >= "0"):
                j += 1
            fields[3] = int(str[i+1:j])
            i = j
        elif str[i] == "l":
            j = i+1
            while(j < len(str) and str[j] <= "9" and str[j] >= "0"):
                j += 1
            fields[4] = int(str[i+1:j])
            i = j
        elif str[i] == "r":
            j = i+1
            while(j < len(str) and str[j] <= "9" and str[j] >= "0"):
                j += 1
            fields[5] = int(str[i+1:j])
            i = j
    return fields


def get_score(fields, IDF):
    score = 0
    for i in range(0, len(fields)):
        score = score + (float(fields[i]) * float(section_weight[i]) * float(IDF))
    return score
            
def def_val():
    return {"field": [0, 0, 0, 0, 0, 0], "score": 0}

def get_word_details(word):
    idx = get_index_file_idx(word)
    index_fname = "index_" + str(idx) + ".txt"
    index_fp = open(os.path.join(abs_index_path, index_fname), "r")
    line = index_fp.readline()
    found = False
    while(line != ""):
        line = line.strip("\n")
        if(line != ""):
            line = line.split("=")
            if(line[0] == word):
                found = True
                break
        line = index_fp.readline()
    word_detail = {"IDF": 0, "doc_count": 0, "freq": 0, "posting_list": {}}
    if found is True:
        word_detail["IDF"] = line[1]
        word_detail["doc_count"] = line[2]
        word_detail["freq"] = line[3]
        docs = line[4].split("|")
        for entry in docs:
            entry = entry.split(" ")
            docID = entry[0]
            fields = extract_field_count(entry[1])
            word_detail["posting_list"][docID] = fields
            word_detail["posting_list"][docID].append(get_score(fields, word_detail["IDF"]))
    return word_detail

    


def process_non_field_query(query):
    #case folding and tokenization
    query = word_tokenize(query.lower())
    #removing stopwords
    query = [word for word in query if word not in stopwords]
    #stemming
    query = [stemmer.stem(word) for word in query]
    word_details = {}
    for word in query:
        word_details[word] = get_word_details(word)
    #set union
    docIDs = set()
    for word in word_details:
        docIDs = docIDs.union(set(word_details[word]["posting_list"].keys()))
    
    max_heap = []
    for docID in docIDs:
        score = 0
        for word in word_details:
            if docID in word_details[word]["posting_list"]:
                score += word_details[word]["posting_list"][docID][-1]
        max_heap.append((-score, docID))
    heapq.heapify(max_heap)
    topK = []
    for i in range(0, K):
        topK.append(heapq.heappop(max_heap)[1])
    return topK

def docID_to_title(docID):
    docID = int(docID)
    title_idx = docID // title_per_file
    title_offset = docID % title_per_file
    title_fname = "title_" + str(title_idx) + ".txt"
    title_fp = open(os.path.join(abs_index_path, title_fname), "r")
    lines = title_fp.readlines()
    title = lines[title_offset].strip("\n")
    return title
    

def process_query(query):
    start = datetime.utcnow()
    # if(len(query) > 2):
    #     if(query[:2] in field_identifier):
    #         is_field_query = True
    # if(is_field_query is False):
    #     topK_docs = process_non_field_query(query)
    # else:
    #     topK_docs = process_field_query(query)

    # skip field queries for now
    if(len(query) > 2):
        if(query[:2] in field_identifier):
            query = query.split(" ")
            for word in query:
                if(word[:2] in field_identifier):
                    word = word[2:]
            query = ' '.join(query)
    
    topK_docs = process_non_field_query(query)
    
    topK_docs_details = []
    for docID in topK_docs:
        topK_docs_details.append([docID, docID_to_title(docID)])

    end = datetime.utcnow()
    return topK_docs_details, (end - start).total_seconds()

def start_interactive():
    global query_in_string
    query_in_string = query_in

def non_interactive():
    start_time = datetime.utcnow()
    global query_in_file
    query_in_file = query_in
    print(query_in_file)
    query_in_fp = open(sys.argv[2], "r")
    out_dir = "out"
    abs_out_dir = os.path.abspath(out_dir)
    if(os.path.isdir(abs_out_dir) == False):
        os.mkdir(abs_out_dir)
    query_out_fname = "query_op.txt"
    query_out_fp = open(os.path.join(abs_out_dir, query_out_fname), "w")

    query_lines = query_in_fp.readlines()
    for line in query_lines:
        line = line.strip("\n")
    for line in query_lines:
        if(line != ""):
            top_docs, time = process_query(line)
            for doc in top_docs:
                docID = doc[0]
                doc_title = doc[1]
                query_out_fp.write(str(docID) + ", " + doc_title + "\n")
            query_out_fp.write("Processing Time: %.2f seconds\n\n" % time)
    
    end_time = datetime.utcnow()
    query_out_fp.write("Total Processing Time: %.2f seconds\n" % (end_time - start_time).total_seconds())
    print("Total Processing Time: %.2f seconds\n" % (end_time - start_time).total_seconds())

    query_in_fp.close()
    query_out_fp.close()


def load_secondary_index():
    secondary_fname = "secondary_index.txt"
    secondary_fp = open(os.path.join(abs_index_path, secondary_fname), "r")
    global secondary_index
    lines = secondary_fp.readlines()
    for line in lines:
        line = line.strip("\n")
        if(line != ""):
            secondary_index.append(line)
    secondary_fp.close()

def main():
    global abs_index_path, input_query, interactive
    abs_index_path = sys.argv[1]
    query_in = sys.argv[2]
    interactive = sys.argv[3]
    load_secondary_index()
    if(interactive == "True"):
        start_interactive()
    else:
        non_interactive()

if __name__ == "__main__":
    main()