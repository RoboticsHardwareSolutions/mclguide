import csv
import os


def get_column(rows, name):
    for i in range(len(rows)):
        for j in range(len(rows[i])):
            if (rows[i][j] == name):
                return i
    raise Exception("Sorry, cannot find ")


def get_row(rows, name):
    for i in range(len(rows)):
        for j in range(len(rows[i])):
            if (rows[i][j] == name):
                return j
    raise Exception("Sorry, cannot find ")


def bom_check_text(rows):
    row = get_row(rows, "Textual description")
    if len(rows) < 2:
        print(" В таблице bom не хватает данных")
        raise SystemExit(1)
    for i in range(1, len(rows)):
        if rows[i][row] == "" or rows[i][row] == " " or rows[i][row] == "M3" or rows[i][row] == "M4":
            print(" В таблице bom есть незаполненные поля Textual description")
            raise SystemExit(1)


def bom_check_articles(rows):
    row = get_row(rows, "Article number")
    for i in range(1, len(rows)):
        if rows[i][row] == "" or rows[i][row] == " ":
            print(" В таблице bom есть незаполненные поля Article number")
            raise SystemExit(1)


def bom_check_correct_articles(rows):
    row = get_row(rows, "Article number")
    list_articles = []
    for i in range(1, len(rows)):
        list_articles.append(rows[i][row].replace(' ', ''))
    has_duplicates = len(list_articles) > len(set(list_articles))
    if has_duplicates:
        print(" В списке ариткулов есть дубликаты !!!")
        print(" Это может быть в том числе вызвано наличием ошибочных пробелов до или после артикула ")
        print(" Требуется исправить в проекте !")
        raise SystemExit(1)


def bom_check_manuf(rows):
    row = get_row(rows, "Manufacturer")
    for i in range(1, len(rows)):
        if rows[i][row] == "" or rows[i][row] == " ":
            print(" В таблице bom есть незаполненные поля Manufacturer")
            raise SystemExit(1)


def bom_check_headers(rows):
    ok = 6
    if rows[0][0] == "Textual description":
        ok -= 1
    if rows[0][1] == "Article number":
        ok -= 1
    if rows[0][2] == "Manufacturer":
        ok -= 1
    if rows[0][3] == "Quantity":
        ok -= 1
    if rows[0][4] == "Unity":
        ok -= 1
    if rows[0][5] == "Designation quantity":
        ok -= 1
    if ok != 0:
        print(" В таблице с bom содержатся неверные названия заголовков столбцов")
        print(
            'Textual description', 'Article number', 'Manufacturer', 'Quantity', 'Unity', 'Designation quantity',
            'Supplier')
        raise SystemExit(1)


def find_bom(bom_directory):
    bom_list = os.listdir(bom_directory)
    for i in bom_list:
        if i.find("parts list") == 0 and i.find(".csv") != -1:
            return i
    return None


def make_rows(reader):
    rows = []
    for row in reader:
        rows.append(row)
    return rows


def bom_check(bom_directory):
    bom = bom_directory + find_bom(bom_directory)
    with open(bom, newline='', encoding='UTF-8', ) as csvfile:
        reader = csv.reader(csvfile, delimiter=';', quotechar='"')
        rows = make_rows(reader)
        bom_check_headers(rows)
        bom_check_text(rows)
        bom_check_articles(rows)
        bom_check_correct_articles(rows)
        bom_check_manuf(rows)
        csvfile.close()
