from qetproject import QETProject
import os


def project_name(vault):
    list = os.listdir(vault)
    name = ""
    found = 0
    for i in list:
        if i.find(".QET") != -1 or i.find(".qet") != -1:
            found += 1
            name = i
    if found == 1:
        return vault + name
    else:
        print("В корневой директории  отсутствует файл проекта или содержится несколько проектов")
        raise SystemExit(1)


def projcheck(vault):
    name = project_name(vault)
    qet_project = QETProject(name)
    elements = qet_project._getListOfElementsByType("elements")
    print(elements)



def get_vault():
    return "/Users/doc/projects/dm/server-cabinet/"


if __name__ == '__main__':
    projcheck(get_vault())
