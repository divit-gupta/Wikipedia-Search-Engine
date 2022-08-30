import sys
import os

bytes_in_GB = 1073741824

def main():
    if(len(sys.argv) != 3):
        print("ERROR: Expected 2 command line arguments, path_to_wiki_dump and required_trimmed_dump_size")
        print("SYNTAX: python trim.py <path_to_dump> <trimmed_size_in_GB>")
        exit(1)

    dump_path = sys.argv[1]
    abs_dump_path = os.path.abspath(dump_path)
    if(os.path.isfile(abs_dump_path) is False):
        print("{dump_path} does not exist")
        exit(1)

    trim_size_GB = sys.argv[2]
    trim_size_B = round(float(trim_size_GB) * bytes_in_GB)

    trim_path = "../data/dump" +( trim_size_GB.replace('.', '_')) + "GB.xml"
    abs_trim_path = os.path.abspath(trim_path)

    dump_fp = open(abs_dump_path, "r")
    trim_fp = open(abs_trim_path, "w")

    while(trim_size_B > 0):
        if(trim_size_B >= bytes_in_GB):
            data = dump_fp.read(int(bytes_in_GB))
            trim_fp.write(data)
            trim_size_B -= bytes_in_GB
        else:
            data = dump_fp.read(int(trim_size_B))
            trim_fp.write(data)
            trim_size_B = 0

    end = "\n  </page>\n</mediawiki>"
    trim_fp.write(end)

    dump_fp.close()
    trim_fp.close()    

if __name__ == "__main__":
    main()