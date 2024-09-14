import sys, os, re, glob
from check_list import check_list
from bom import bom_check


def get_vault():
    arg = sys.argv[1]
    vault = (arg, arg + "/")[arg[len(arg) - 1] != "/"]
    return vault


if __name__ == '__main__':

    print("--------------------------------------------------------------------------")
    pattern = re.compile(r"^[A-Z]{3}\.\d{6}\.\d{3}\.\d{1}")
    for dirpath, _, filenames in os.walk('/Users/doc/Nextcloud/КД/'):
        for filename in filenames:
            if pattern.search(filename) is None:
                print("- [ ] " + os.path.join(dirpath, filename).replace("/Users/doc/", ""))

    # print("--------------------------------------------------------------------------")
    # values = {}
    # pattern = re.compile(r"^[A-Z]{3}\.\d{6}\.\d{3}\.\d{1}")
    # for dirpath, _, filenames in os.walk('/Users/doc/Nextcloud/КД/CMR'):
    #     for filename in filenames:
    #         if pattern.search(filename):
    #             name = filename[0:16]
    #             values[name] = dirpath
    # print(values.count())
    # print(values.items())
    # print()

    # print("--------------------------------------------------------------------------")
    # for file_path in glob.iglob('/Users/doc/Nextcloud/КД/CMR/' + '**/*.xls', recursive=True):
    #     print(file_path.replace("/Users/doc", "- [ ] "))
