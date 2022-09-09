
import re
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords as SW
from nltk import word_tokenize

# capping
body_load_factor = 0.5
MAX_WORD_CAP = 30



class Preprocess:
    def __init__(self):
        # stats
        self.TotalWordsEncountered = 0

        self.stemmer = PorterStemmer()
        self.stopwords = set(SW.words('english'))
        self.externalLinksPattern = r"==External links==\n[\s\S]*?\n\n"
        self.referencesPattern = r"== ?references ?==(.*?)\n\n"
        self.removeSymbolsPattern = r"[~`!@#$%-^*+{\[}\]\|\\<>/?]"
        self.filter = set(['(', '{', '[', ']', '}', ')', '=', '|', '?', ',', '+', '\'', '\\', '*', '#', ';', '!', '\"', '%'])
        self.wiki_pattern = {
            "Infobox": "{{Infobox",
            "infobox" : "{{infobox",
            "category" : "\[\[Category:\s*(.*?)\]\]",
            "wiki_links": "\[\[(.*?)\]\]",
            "comments" : "<--.*?-->",
            "styles" : "\[\|.*?\|\]",
            "curly_braces": "{{.*?}}",
            "square_braces": "\[\[.*?\]\]",
            "references": "<ref>.*?</ref>",
            "url": "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
            "www": "www\.(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        }

# ===============================================================================
# ============================= UTILITY FUNCTIONS ===============================
# ===============================================================================

    def remove_all_urls(self, text):
        regex = re.compile(self.wiki_pattern["url"])
        text = re.sub(regex, ' ', text)
        regex = re.compile(self.wiki_pattern["www"])
        text = re.sub(regex, ' ', text)
        return text
    
    def remove_all_tags(self, text):
        tag_regex = re.compile("<.*?>")
        return re.sub(tag_regex, '', text)

    def filter_content(self, text):
        text = text.strip()
        filters = self.filter
        if len(text) == 0:
            return ""
        if len(set(text).intersection(filters)) == 0:
            return text
        for f in filters:
            text = text.replace(f, ' ')
        return text

    def strip_footers(self, text):
      labels = ["References", "Further reading", "See also", "Notes"]
      for l in labels:
         regex = "==%s==" % (labels)
         found = re.search(regex, text)
         if found is not None:
            text = text[0:found.start()-1]
      return text 

# ===============================================================================
# ========================= EXTRAACT CONTENT METHODS ============================
# ===============================================================================

    def extract_infobox_content(self, text):
        if len(text) == 0:
            return text, ""
        infobox_content = ""
        start_idx = text.find(self.wiki_pattern["infobox"])
        pattern_len = len(self.wiki_pattern["infobox"])
        if start_idx < 0:
            return text, infobox_content
        start_idx += pattern_len
        end = len(text)
        bracket_cnt = 2
        for idx in range(start_idx, end):
            if text[idx] == '{':
                bracket_cnt += 1
            elif text[idx] == '}':
                bracket_cnt -= 1
            if bracket_cnt == 0:
                break
        new_text = text[0:start_idx-1] + text[idx+1:-1]
        infobox_content = text[start_idx:idx-1]
        infobox_content = self.remove_all_urls(infobox_content)
        infobox_content = self.filter_content(infobox_content)
        infobox_content = self.remove_all_tags(infobox_content)
        return new_text, infobox_content

    def extract_Infobox_content(self, text):
        if len(text) == 0:
            return text, ""
        Infobox_content = ""
        start_idx = text.find(self.wiki_pattern["Infobox"])
        pattern_len = len(self.wiki_pattern["Infobox"])
        if start_idx < 0:
            return text, Infobox_content
        start_idx += pattern_len
        end = len(text)
        bracket_cnt = 2
        for idx in range(start_idx, end):
            if text[idx] == '{':
                bracket_cnt += 1
            elif text[idx] == '}':
                bracket_cnt -= 1
            if bracket_cnt == 0:
                break
        new_text = text[0:start_idx-1] + text[idx+1:-1]
        Infobox_content = text[start_idx:idx-1]
        Infobox_content = self.remove_all_urls(Infobox_content)
        Infobox_content = self.filter_content(Infobox_content)
        Infobox_content = self.remove_all_tags(Infobox_content)
        return new_text, Infobox_content

    def extract_category_content(self, text):
        category_regex = re.compile(self.wiki_pattern["category"], re.IGNORECASE)
        category_content = re.findall(category_regex, text)
        category_content = ' '.join(category_content)
        category_content = self.remove_all_urls(category_content)
        category_content = self.filter_content(category_content)
        category_content = self.remove_all_tags(category_content)
        new_text = re.sub(category_regex, ' ', text)
        return new_text, category_content

    def extract_ext_links_content(self, text):
        ext_link_content = re.findall(self.externalLinksPattern, text, flags= re.IGNORECASE)
        ext_link_content = ' '.join(ext_link_content)
        ext_link_content = ext_link_content[20:]
        ext_link_content = re.sub('[|]', ' ', ext_link_content)
        ext_link_content = re.sub('[^a-zA-Z ]', ' ', ext_link_content) 
        return text, ext_link_content

    def extract_ref_content(self, text):
        ref_content = re.findall(self.referencesPattern, text, flags=re.DOTALL | re.MULTILINE | re.IGNORECASE)
        ref_content = ' '.join(ref_content)
        ref_content = re.sub(self.removeSymbolsPattern, ' ', ref_content)
        return text, ref_content

    def extract_body_content(self, text):
        # uncomment for drop body
        # text = text[0 : int(len(text) * body_load_factor)]

        regex = re.compile(self.wiki_pattern["comments"])
        body_content = re.sub(regex, ' ', text)
        regex = re.compile(self.wiki_pattern["styles"])
        body_content = re.sub(regex, ' ', body_content)
        regex = re.compile(self.wiki_pattern["references"])
        body_content = re.sub(regex, ' ', body_content)
        body_content = self.remove_all_tags(body_content)
        regex = re.compile(self.wiki_pattern["curly_braces"])
        body_content = re.sub(regex, ' ', body_content)
        regex = re.compile(self.wiki_pattern["square_braces"])
        body_content = re.sub(regex, ' ', body_content)
        #remove links
        body_content = self.remove_all_urls(body_content)
        #remove footers
        body_content = self.strip_footers(body_content)
        return body_content
        # return body_content[0 : int(len(body_content) * body_load_factor)]

# ===============================================================================
# ============================= DRIVER FUNCTIONS ================================
# ===============================================================================

    def process(self, text):
        text = self.filter_content(''.join(text)).lower()
        #word tokenization
        remove_idx = []
        text = word_tokenize(text)
        
        # for stat
        self.TotalWordsEncountered += len(text)

        text = [word for word in text if len(word) < MAX_WORD_CAP and word not in self.stopwords]

        #stemming of words
        text = [self.stemmer.stem(w) for w in text]
        return text
    
    def process_title(self, raw_title):
        return self.process(raw_title)

    def process_text(self, text):
        text, raw_infobox = self.extract_infobox_content(text)
        text, raw_Infobox = self.extract_Infobox_content(text)
        raw_infobox = raw_infobox + " " + raw_Infobox
        text, raw_category = self.extract_category_content(text)
        text, raw_link = self.extract_ext_links_content(text)
        text, raw_ref = self.extract_ref_content(text)
        raw_body = self.extract_body_content(text)
        return self.process(raw_infobox), self.process(raw_body), self.process(raw_category), self.process(raw_link), self.process(raw_ref)