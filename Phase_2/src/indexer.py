import xml.sax
import sys
from datetime import datetime
import os

class WikiHandler(xml.sax.ContentHandler):
    # initialize the class
    def __init__(self):
        pass
    def startElement(self, tag, attrs):
        pass
    def endElement(self, tag):
        pass
    def characters(self, content):
        pass

def main():
    if(len(sys.argv) != 4):
        print("Invalid number of arguments")
        print("Expected 3 arguments: <path_to_xml_dump> <path_to_index_folder> <stat_file_name>")
        exit(1)

    global start_time, abs_xml_path, abs_index_path

    start_time = datetime.utcnow()
    abs_xml_path = os.path.abspath(sys.argv[1])
    abs_index_path = os.path.abspath(sys.argv[2])
    if(os.path.isdir(abs_index_path) is False):
        os.mkdir(abs_index_path)

    stat_file = sys.argv[3]

    if(not os.path.isfile(abs_xml_path)):
        print("Invalid xml file path")
        exit(1)
    
    if(not os.path.isdir(abs_index_path)):
        print("Invalid index folder path")
        exit(1)
    
    end_time = datetime.utcnow()

    primary_index_time = (end_time - start_time).total_seconds()

    print("Primary Index creation time:", primary_index_time, "seconds")
    return

if __name__ == "__main__":
    main()