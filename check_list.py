import os


def files_list_checker_doc(root_list):
    try:
        root_list.index("doc")
    except ValueError:
        print("Папка /doc отсутствует в корне репозитория")
        raise SystemExit(1)


def files_list_checker_schematics_previews(root_list):
    try:
        root_list.index("schematic_previews")
    except ValueError:
        print("Папка /doc/schematic_previews отсутствует в корне репозитория")
        raise SystemExit(1)


def delete_if_found(root_list, name):
    try:
        index = root_list.index(name)
    except ValueError:
        index = None
    if index is not None:
        root_list.remove(name)


def get_project_name(root_dir):
    name = ""
    found = 0
    for i in root_dir:
        if i.find(".QET") != -1 or i.find(".qet") != -1:
            found += 1
            name = i
    if found == 1:
        return name
    else:
        print("В корневой директории  отсутствует файл проекта или содержится несколько проектов")
        raise SystemExit(1)


def get_spec(spec_dir):
    name = ""
    found = 0
    for i in spec_dir:
        if i.find(".csv") != -1 or i.find(".CSV") != -1:
            found += 1
            name = i
    if found == 1:
        return name
    else:
        print("В  директории  /doc  остустствует файл спецификации или содержится несколько файлов")
        raise SystemExit(1)


def check_previews(preview_dir):
    name = ""
    found = 0
    for i in preview_dir:
        if i.find(".png") != -1 or i.find(".PNG") != -1:
            found += 1
            name = i
    if found >= 3:
        return name
    else:
        print("В  директории  /doc/schematic_previews  остустствют превью листов схемы в формате .png")
        raise SystemExit(1)


def get_sch_pdf(doc_dir):
    name = ""
    found = 0
    for i in doc_dir:
        if i.find(".pdf") != -1 or i.find(".PDF") != -1:
            found += 1
            name = i
    if found == 1:
        return name
    else:
        print("В  директории  /doc  остустствует файл схемы или содержится несколько файлов")
        raise SystemExit(1)


def checker_trash_root(root_list):
    root_list.remove("doc")
    root_list.remove(get_project_name(root_list))
    delete_if_found(root_list, 'README.md')
    delete_if_found(root_list, 'Readme.md')
    delete_if_found(root_list, '.git')
    delete_if_found(root_list, '.gitlab-ci.yml')
    delete_if_found(root_list, ".gitignore")
    delete_if_found(root_list, '.DS_Store')
    delete_if_found(root_list, 'simulation')
    delete_if_found(root_list, '.gitmodules')
    delete_if_found(root_list, 'software')
    delete_if_found(root_list, "firmware")
    if len(root_list) != 0:
        print("В корне репозитория содержится 'мусор' :")
        print(root_list)
        raise SystemExit(1)


def checker_trash_doc(doc_list):
    delete_if_found(doc_list, get_spec(doc_list))
    delete_if_found(doc_list, get_sch_pdf(doc_list))
    delete_if_found(doc_list, 'schematic_previews')
    delete_if_found(doc_list, '.DS_Store')
    if len(doc_list) != 0:
        print("В папке /doc репозитория содержится 'мусор' :")
        print(doc_list)
        raise SystemExit(1)


def check_list(vault):
    list = os.listdir(vault)
    files_list_checker_doc(list)
    list = os.listdir(vault + "doc")
    files_list_checker_schematics_previews(list)
    list = os.listdir(vault)
    checker_trash_root(list)
    list = os.listdir(vault + "doc")
    get_spec(list)
    list = os.listdir(vault + "doc")
    get_sch_pdf(list)
    list = os.listdir(vault + "doc")
    checker_trash_doc(list)
    list = os.listdir(vault + "doc/schematic_previews/")
    check_previews(list)


def get_vault_test():
    return "/Users/doc/projects/dm/server-cabinet/"


if __name__ == '__main__':
    check_list(get_vault_test())
