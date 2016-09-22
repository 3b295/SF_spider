# -*- coding: utf-8 -*-
import asyncio
from asyncio import Queue
import aiohttp
import re
from lxml import etree

INDEX = 'http://book.sfacg.com/'
q = Queue()

async def work(session, url):
    async with session.get(url) as respon:
        try:
            assert respon.status == 200
            text = await respon.text()
            html = etree.HTML(text)
            xpath = '/html/body/div[2]/div[3]/ul//a'
            result = html.xpath(xpath)
            down_list = [[x.text if x.text else 'error', x.xpath('./@href')[0]] for x in result]
            print('[*]down_list: {}'.format(len(down_list)))
            return down_list
        except AssertionError:
            print('[error] {} - {}'.format(url, respon.status))
            exit()


async def downer(session, result_list):
    global q
    while True:
        try:
            name, url = await q.get()
            print(name, url)
            async with session.get(INDEX + url) as response:
                assert response.status == 200
                html = await response.text()
                tree = etree.HTML(html)

                raw_list = [x.text for x in tree.xpath('//*[@id="ChapterBody"]//p')]
                text = '\n'.join(filter(lambda x: x and re.search(r'[^\n ]', x), raw_list))

                result_list.append([url, text])
        except AssertionError:
            print('[error] {} - {}'.format(url, response.status))
        finally:
            try:
                q.task_done()
            except ValueError:
                if q.empty():
                    print('q empty')


async def main(loop, url):
    async with aiohttp.ClientSession(loop=loop) as session:
        global q
        down_list = await work(session, url)

        for i in down_list:
            await q.put(i)
        content_list = []
        tasks = [asyncio.ensure_future(downer(session, content_list)) for i in range(20)]
        await q.join()
        for task in tasks:
            task.cancel()
        print('[*]down over')

        index = [x[0] for x in down_list]
        order = [x[1] for x in down_list]
        content_list.sort(key=lambda x: order.index(x[0]))
        with open('result.txt', 'wb') as file:
            file.write('\n'.join(index).encode('utf-8'))
            index.reverse()
            for url, content in content_list:
                file.write('\n{}\n\n\n'.format(index.pop()).encode('utf-8'))
                file.write(content.encode('utf-8'))

if __name__ == '__main__':
    import time
    url = 'http://book.sfacg.com/Novel/50076/MainIndex/'
    start = time.time()
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main(loop, url))
    finally:
        if loop:
            loop.close()
        print(time.time() - start)
