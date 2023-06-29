#!/usr/bin/env python3
import os
import shutil
import zipfile

import yaml
from colorama import Fore, init
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from tqdm import tqdm

init()
gauth = GoogleAuth()
gauth.LocalWebserverAuth()
ascii_art = """


                                              .-+:        
                                          .:=****::       
                                       :-+******+:::.     
                                   .-=**********=-::::    
                                 .***********+=------::.  
                                .*#********+=----=====--: 
                                *##*****+=--=============:
                               *###***+==================.
                              *#####===================== 
                             +######+===================- 
                            +#######*+==================: 
                            :#######**+=================  
                             -######***+===============-  
                              =#####****+==============:  
                               +####*****+=============   
                                *####*****+===========-   
                                 *###******+==========:   
                                 .*##*******+=========    
                                  :##********+====+++=    
                                   :#*********+++++++:    
                                    -**********++++++     
                                     :=+********++++-     
                                         .:-=+***++-      
                                
                                  
           __              _        __    _                         _____    ____    ____ 
  ____    / /_    _____   (_)  ____/ /   (_)  ____ _   ____        /__  /   /  _/   / __ |
 / __ \  / __ \  / ___/  / /  / __  /   / /  / __ `/  / __ \         / /    / /    / /_/ /
/ /_/ / / /_/ / (__  )  / /  / /_/ /   / /  / /_/ /  / / / /        / /__ _/ /    / ____/ 
\____/ /_.___/ /____/  /_/   \__,_/   /_/   \__,_/  /_/ /_/        /____//___/   /_/      
                                                                                          

"""
ascii_art = ascii_art.replace("@", " ")


def print_colored_ascii(ascii_art, color):
    print(color+ascii_art + Fore.RESET)


# Получаем путь к текущей рабочей директории
current_directory = os.getcwd()

# Формируем полный путь к файлу конфигурации
config_file_path = os.path.join(current_directory, "config.yml")


def create_config_file():
    config_data = {}
    config_data["source_folder"] = input(
        "Введите путь к папке исходных файлов: ")
    config_data["destination_folder"] = input(
        "Введите путь к папке назначения: ")
    config_data["archive_name"] = input("Введите имя архива: ") + ".zip"

    with open(config_file_path, "w") as config:
        yaml.safe_dump(config_data, config)


if not os.path.exists(config_file_path) or os.stat(config_file_path).st_size == 0:
    print(f"Конфиг не найден")
    print(f"Создаем конфиг")
    create_config_file()

with open(config_file_path, "r") as config_file:
    config = yaml.safe_load(config_file)

print(f"Загружаю конфиг")
# Извлечение значений путей из конфигурации
source_folder = config["source_folder"]
destination_folder = config["destination_folder"]
archive_name = config["archive_name"]


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def create_archive():
    if not os.path.exists(destination_folder):
        # Если папка не существует, создаем ее
        os.makedirs(destination_folder)

    # Проверка существования файла в папке "Obsidian"
    archive_path = os.path.join(destination_folder, archive_name)
    if os.path.isfile(archive_path):
        # Если файл существует, удаляем его
        os.remove(archive_path)

    print(Fore.BLUE + "Создание архива..." + Fore.RESET)

    # Создание архива ZIP с максимальным сжатием
    zipf = zipfile.ZipFile(
        archive_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9)

    total_files = 0
    for root, dirs, files in os.walk(source_folder):
        total_files += len(files)

    with tqdm(total=total_files, unit='файлов') as pbar:
        for root, dirs, files in os.walk(source_folder):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(
                    file_path, source_folder))
                pbar.update(1)

    zipf.close()

    print(Fore.GREEN + "Архив успешно создан и отправлен в папку Obsidian." + Fore.RESET)


def extract_archive():
    print(Fore.BLUE + "Разархивирование архива..." + Fore.RESET)
    if os.path.exists(source_folder):
        shutil.rmtree(source_folder)

    # Создаем директорию source_folder
    os.makedirs(source_folder)
    with zipfile.ZipFile(os.path.join(destination_folder, archive_name), 'r') as zip_ref:
        zip_ref.extractall(source_folder)
    print(Fore.GREEN +
          f"Архив успешно разархивирован в папку {source_folder}." + Fore.RESET)


def download_file_from_gdrive():
    archive_path = os.path.join(destination_folder, archive_name)
    print(Fore.YELLOW + f"Удаление старого файла..." + Fore.RESET)
    if os.path.isfile(archive_path):
        #    Если файл существует, удаляем его
        os.remove(archive_path)
    print(Fore.YELLOW + f"Загрузка нового файла" + Fore.RESET)
    try:
        drive = GoogleDrive(gauth)

        # Получение списка файлов в корневой папке
        file_list = drive.ListFile(
            {'q': "'root' in parents and trashed=false"}).GetList()

        found = False
        for file in file_list:
            if file['title'] == archive_name:
                # Скачивание файла
                file.GetContentFile(os.path.join(
                    destination_folder, archive_name))
                print(Fore.GREEN +
                      f"Файл {archive_name} успешно загружен!"+Fore.RESET)
                found = True
                break

        if not found:
            print(
                Fore.RED + f"Файл {archive_name} не найден в Google Drive." + Fore.RESET)

    except Exception as ex:
        print("Возникла ошибка при загрузке файла из Google Drive:", str(ex))


def delete_files_from_gdrive():
    drive = GoogleDrive(gauth)
    try:
        file_list = drive.ListFile({'q': f"title='{archive_name}'"}).GetList()

        if len(file_list) > 0:
            progress_bar = tqdm(total=len(file_list), desc='Удаление файла')

            for file in file_list:
                file.Delete()
                progress_bar.update(1)
                progress_bar.set_postfix(file=file['title'])

            progress_bar.close()
            print(
                Fore.GREEN + f"Все файлы с именем '{archive_name}' были успешно удалены." + Fore.RESET)
        else:
            print(Fore.YELLOW +
                  f"Файлы с именем '{archive_name}' не найдены." + Fore.RESET)
    except Exception as ex:
        print(Fore.RED + "Возникла ошибка при удалении файлов:" +
              str(ex) + Fore.RESET)


def upload_file_to_gdrive():
    try:
        drive = GoogleDrive(gauth)

        # Get the list of files in the destination folder
        files = os.listdir(destination_folder)

        # Initialize the progress bar
        progress_bar = tqdm(total=len(files), desc='Загрузка файла')

        for archive_name in os.listdir(destination_folder):

            my_file = drive.CreateFile({'title': f'{archive_name}'})
            my_file.SetContentFile(os.path.join(
                destination_folder, archive_name))
            my_file.Upload()
            print(Fore.LIGHTGREEN_EX +
                  f'Файл {archive_name} был успешно загружен!' + Fore.RESET)
            progress_bar.update(1)
            progress_bar.set_postfix(file=archive_name)
        progress_bar.close()
        return print(Fore.GREEN + 'Все файлы успешно загружены' + Fore.RESET)
    except Exception as _ex:
        return print(Fore.RED + 'Возникла ошибка' + Fore.RESET)


def main():
    clear_screen()
    print_colored_ascii(ascii_art, Fore.MAGENTA)

    print("Выберите действие:")
    print("1. Создать архив")
    print("2. Добавить хранилище")
    print("3. Заполнить конфигурационный файл заново: ")
    choice = input("Введите номер действия (1,2 и 3): ")

    if choice == "1":
        create_archive()
        upload_choice = input(
            "Хотите ли вы загрузить архив на Google Drive? (y/n): ")
        if upload_choice.lower() == "y":
            print(Fore.YELLOW + f"Удаление старой версии файла..." + Fore.RESET)
            delete_files_from_gdrive()
            print(Fore.YELLOW+f"Загрузка новой версии файла..."+Fore.RESET)
            upload_file_to_gdrive()
        elif upload_choice.lower() == "n":
            print(Fore.YELLOW + "Архив не будет загружен на Google Drive." + Fore.RESET)
        else:
            print("Некорректный выбор.")

    elif choice == "2":
        download_choise = input(
            "Хотите загрузить архив с Google Drive? (y/n): ")
        if download_choise.lower() == "y":
            download_file_from_gdrive()
            extract_archive()
        if download_choise.lower() == "n":
            extract_archive()
    elif choice == "3":
        create_config_file
    else:
        print(Fore.RED + "Неверный выбор. Выберите 1, 2 или 3." + Fore.RESET)


if __name__ == "__main__":
    main()
