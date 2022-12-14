import datetime
import time
import json
from pprint import pprint
import configparser
import requests
from tqdm import tqdm
import random

def main():

    class VkUser():
        config = configparser.ConfigParser()
        config.read("settings.ini")
        token_vk = config["Vk"]["token_VK"]

        url = 'https://api.vk.com/method/'

        def __init__(self, token_vk, version):
            self.params = {
                'access_token': token_vk,
                'v': version}

        def input_user_data(self):
            screen_name_or_id = input("Введите screen_name или id в Контакте  ")
            if screen_name_or_id.isdigit():
                self.object_id = screen_name_or_id
            else:
                utils_url = self.url + 'utils.resolveScreenName'
                params = {
                    'screen_name': screen_name_or_id,
                    'access_token': self.token_vk,
                    'v': '5.131'}
                response = requests.get(utils_url, params=params)
                #print(response.json())
                self.object_id = str(response.json()['response']['object_id'])
                print(f'id {self.object_id}')

            album = input("Откуда скачать фотографии?\nфотографии со стены(жми 1)\nфотографии профиля(жми 2)\n"
                             "сохраненные фотографии(жми 3)\n")
            if album == '1':
                self.album_id = 'wall'
            if album == '2':
                self.album_id = 'profile'
            if album == '3':
                self.album_id = 'saved'

            self.count_photo = input('По сколько фотографий скачивать за раз?  ')


        def get_photos(self):
            global result
            global  list_like_date_url_photo
            global  sorted_sizes_photo
            list_like_date_url_photo = []
            sorted_sizes_photo = []
            dict_photo = {}
            name_date_list = []
            group_photos_get = self.url + 'photos.get'
            photos_get_params = {
                'owner_id': self.object_id,
                'album_id': self.album_id,
                'extended': '1',
                'count': self.count_photo
                }
            result = requests.get(group_photos_get, params={**self.params, **photos_get_params})
            pprint(result.json())

            for element in result.json()["response"]["items"]:
                sorted_sizes_photo.append(sorted(element['sizes'], key=lambda x: x['height']))
                likes = element["likes"]["count"]
                date = datetime.datetime.fromtimestamp(element["date"]).strftime("%Y_%m_%d_%H_%M_%S")
                if likes not in name_date_list:
                    name = f"{likes}"
                    name_date_list.append(likes)
                else:
                    name = f"{likes}_{date}"
                    name_date_list.append(likes)
                for el in sorted_sizes_photo:
                    #print(el[-1]['url'])
                    dict_photo = {"name": name, "url": el[-1]['url']}
                list_like_date_url_photo.append(dict_photo)
            #print(list_like_date_url_photo)


    class Yandex():
        config = configparser.ConfigParser()
        config.read("settings.ini")
        token_yandex = config["Yandex"]["token_Yandex"]

        base_host = 'https://cloud-api.yandex.net'

        def __init__(self, token):
            self.token = Yandex.token_yandex

        def get_headers(self):
            return {
                'Content-Type': "application/json",
                'Authorization': f'OAuth {self.token_yandex}'
            }

        def _get_upload_link(self, path):
            uri = '/v1/disk/resources/upload/'
            request_url = self.base_host + uri
            params = {'path': path, 'overwrite': True}
            response = requests.get(request_url, headers=self.get_headers(), params=params)
            return response.json()["href"]

        def add_directory(self, path):
            uri = '/v1/disk/resources/'
            request_url = self.base_host + uri
            params = {'path': path}
            response = requests.put(request_url, headers=self.get_headers(), params=params)
            return response.json()

        def upload_to_disk(self, local_path, yandex_path):
            upload_url = self._get_upload_link(yandex_path)
            response = requests.put(upload_url, data=open(local_path, 'rb'), headers=self.get_headers())

        def upload_from_internet(self):
            uri = '/v1/disk/resources/upload/'
            request_url = self.base_host + uri

            #сохраним фото на яндекс диск с использованием прогресс-бар для отслеживания процесса программы
            print()
            print("резервное копирование фотографий....")
            for element in tqdm(list_like_date_url_photo, colour='green', ncols=100):
                time.sleep(random.uniform(0.2, 1))
                params = {'url': element['url'], 'path': f'photo_archive_vk/{element["name"]}'}
                response = requests.post(request_url, params=params, headers=self.get_headers())
            print(f"копирование успешно завершено, загружено {len(list_like_date_url_photo)} фотографий")


    vk_client = VkUser(VkUser.token_vk, "5.131")
    vk_client.input_user_data()
    vk_client.get_photos()

    ya = Yandex(Yandex.token_yandex)
    ya.add_directory('photo_archive_vk')
    ya.upload_to_disk('requirements.txt', '/photo_archive_vk/requiremеnts.txt')
    ya.upload_from_internet()

    # Сохраним информацию по сохранненым фотографиям на yandex_disk - в файл json
    def save_info_photos():
        list_info_photos = []
        for element in result.json()["response"]["items"]:
            for el in sorted_sizes_photo:
                element['sizes'] = el[-1]
            list_info_photos.append(element)
            with open("photos_in_yandex_disk.json", "w") as file:
                json.dump(list_info_photos, file, ensure_ascii=False, indent=2)
    save_info_photos()

if __name__ == "__main__":
    main()

