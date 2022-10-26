from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import BD
import re
import os
from datetime import datetime

FOLDER = 'YOUR GOOGLE DRIVE FOLDER NAME'

with open('images_location.txt', 'r') as f:
    LOCAL_IMAGES_FOLDER = f.read()

MIMETYPES = {
        # Drive Document files as MS dox
        'application/vnd.google-apps.document': 'text/plain',
        # Drive Sheets files as MS Excel files.
        'application/vnd.google-apps.spreadsheet': 'text/csv'
  }

gauth = GoogleAuth()
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)

def _get_folder_ID(folder_name):
    file_list = drive.ListFile({'q': f"'root' in parents and trashed=false"}).GetList()

    for file in file_list:
        if file['title'] == folder_name:
            return file['id']

MAMA_FOLDER_ID = _get_folder_ID(FOLDER)

def _get_permissions(file):
    download_mimetype = MIMETYPES[file['mimeType']]
    data = file.GetContentString(mimetype=download_mimetype)
    data = data.split('\r\n')
    BD.add_permissions(data)

def _get_hello_text(file):
    download_mimetype = MIMETYPES[file['mimeType']]
    data = file.GetContentString(mimetype=download_mimetype)
    BD.add_hello_text(data)

def _get_menu(folder):
    lister = drive.ListFile({'q': f"'{folder['id']}' in parents and trashed=false"}).GetList()
    cur_time = datetime.now()
    cur_year = cur_time.year

    for file in lister:
        local_filename = file['title']
        date_split = re.findall(r'\d\d', local_filename)
        date = str(cur_year) + '-' + date_split[1] + '-' + date_split[0]
        if file['mimeType'] == 'application/vnd.google-apps.document':
            download_mimetype = MIMETYPES[file['mimeType']]
            text = file.GetContentString(mimetype=download_mimetype)
            BD.add_discription_date(date, text)
        elif re.fullmatch(r'\d{2}\.\d{2}.*', file['title']):
            local_filename = LOCAL_IMAGES_FOLDER + local_filename
            file.GetContentFile(filename=local_filename)
            BD.add_photo(date, local_filename)
            os.remove(local_filename)

def _add_data_to_Drive(file_name, func):
    data = func()

    my_file = drive.CreateFile({'title': file_name,
                                'mimeType': 'text/csv',
                                'parents': [{'id': MAMA_FOLDER_ID}]})
    my_file.SetContentString(data.to_csv())
    my_file.Upload({'convert': True})

def add_new_data_to_DB():
    lister = drive.ListFile({'q': f"'{MAMA_FOLDER_ID}' in parents and trashed=false"}).GetList()
    for file in lister:
        if file['title'] == 'permissions file':
            _get_permissions(file)
        elif file['title'] == 'hello text file':
            _get_hello_text(file)
        elif file['title'] == 'actual menu file':
            _get_menu(file)

def update_clients_orders_wishes():
    file_wishes = 'extra wishes from clients file'
    file_orders = 'actual orders file'
    file_clients = 'clients file'
    files = (file_wishes, file_orders, file_clients)

    lister = drive.ListFile({'q': f"'{MAMA_FOLDER_ID}' in parents and trashed=false"}).GetList()
    for file in lister:
        if file['title'] in files:
            file.Trash()

    

    _add_data_to_Drive(file_name = file_clients, func = BD.get_users)
    _add_data_to_Drive(file_name = file_orders, func = BD.get_actual_orders)
    _add_data_to_Drive(file_name = file_wishes, func = BD.get_extra_wishes)

if __name__ == '__main__':
    update_clients_orders_wishes()