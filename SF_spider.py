# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests

from collections import OrderedDict
import os
import threading
from termcolor import colored, cprint
from IPython import embed

try:
    import cPickle as pickle
except:
    import pickle


############################################
#   title                           -> 书名
#   reel_dict                       -> 卷的字典
#       name: chapter_msg_list
#   chapter_msg_list                -> 一个卷中章节的list
#       [{name: xxx, url: xxx}
#       ...]
############################################
class Download_SF:
    isDownVip = False
    root_url = 'http://book.sfacg.com'
    pool_count = 6

    title = None
    reel_dict = OrderedDict()

    def run(self, url):
        self.find_download_link(url).download().write_text()

    def analyze(self, soup):
        cprint('[*] start analyze html ...', color='green')

        self.title = soup.body.find_all(class_='wrap')[1].h1.text
        plate_top = soup.find_all(class_='plate_top')[0]

        for title_tree, content_tree in zip(plate_top.find_all(class_='list_menu_title'),
                                            plate_top.find_all(class_='list_Content')):
            reel = title_tree.text.split('\n')[0]
            chapter_msg_list = []
            for x in content_tree.find_all('li'):
                chapter_msg_list.append(
                    {'name': x.span.text + x.a.text if x.span else x.a.text, 'url': self.root_url + x.a['href']})

            if not self.isDownVip:
                chapter_msg_list = list(
                    filter(lambda cp_msg: not cp_msg['name'].strip().startswith('VIP'), chapter_msg_list))

            self.reel_dict[reel] = chapter_msg_list

    @staticmethod
    def filter_file_name(name):
        """用于windows规则
        """
        for s in '<>/\|:""*?\t':
            name = name.replace(s, ' ')
        name = name.strip()
        return name[:254] if len(name) > 255 else name

    def find_download_link(self, url):
        respon = requests.get(url)
        if respon.status_code == 200:
            soup = BeautifulSoup(respon.content.decode('utf-8'))
        else:
            print('http status code: {}'.format(respon.status_code))
            return
        self.analyze(soup)
        return self

    def download(self):
        cprint('[*] start download ...', color='green')
        root_path = os.getcwd() + '/' + self.title
        if not os.path.isdir(root_path):
            os.mkdir(root_path)

        threads = []
        for chapter_msg_list in self.reel_dict.values():
            for cha in chapter_msg_list:
                thr = threading.Thread(target=self.chapter_spider, args=[cha])
                threads.append(thr)
                thr.start()

        for t in threads:
            t.join()
        cprint('[*] download is OK!', color='green')
        return self

    @staticmethod
    def chapter_spider(cha):
        cprint('[-] start download  {} ..'.format(cha['name']), color='grey')
        respon = requests.get(cha['url'])
        soup = BeautifulSoup(respon.content.decode('utf-8'))

        span = soup.body.find_all(class_='content_left2')[0].span
        if span.img:
            imgs = span.find_all('img')
            for index, img in enumerate(imgs):
                re = requests.get(img['src'])
                img_content = re.content
                img_type = img['src'].split('.')[-1]
                img_name = cha['name'] if index == 0 else cha['name'] + str(index + 1)
                img_filename = img_name + '.' + img_type
                with open(img_filename, 'bw') as file:
                    file.write(img_content)
        else:
            contents = span.contents
            text = ''
            for con in contents:
                if con.name == 'br':
                    text += '\n'
                elif con.name == 'p':
                    text += con.text
                    text += '\n'
                else:
                    text += str(con)

                cha['text'] = text

    def write_text(self):
        file_path = os.getcwd() + '\\' + self.filter_file_name(self.title) + '.txt'
        with open(file_path, 'w', encoding='utf-8') as file:
            index = self.title + '\n\n\n\n\n\n\n\n'
            for name in self.reel_dict:
                index += name
                index += '\n'

            index += 'r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n'
            file.write(index)

            for name, chas in self.reel_dict.items():
                chapter_index = name
                for cha in chas:
                    chapter_index += cha['name']
                    chapter_index += '\n'
                chapter_index += '\n\n\n\n\n\n\n\n\n'
                file.write(chapter_index)

                text = ''
                for cha in chas:
                    text += cha['name']
                    text += '\n'
                    if 'text' in cha:
                        text += cha['text']
                    text += '\n\n\n\n\n\n\n\n'
                file.write(text)

            file.write('\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n(>.<)')
        return self


def main(url):
    Download_SF().run(url)


if __name__ == '__main__':
    main('http://book.sfacg.com/Novel/49238/MainIndex/')
