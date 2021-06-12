import requests
import shutil
import asyncio
import aiohttp
import zipfile
from io import BytesIO


def get_rsp(host_url, query=None, safe_check=True, method="get", **kwargs):
    rsp = getattr(requests, method)(host_url, params=query, **kwargs)
    if safe_check:
        assert rsp.status_code == 200, str(rsp.status_code) + str(query)
    return rsp


def save_image_from_rsp(respond, file_name):
    with open(file_name, 'wb') as out_file:
        respond.raw.decode_content = True
        shutil.copyfileobj(respond.raw, out_file)


async def fetch_resp(url, param, session: aiohttp.ClientSession, **kwargs):
    resp = await session.request(method="GET", url=url, params=param, ssl=False, **kwargs)
    try:
        resp = await resp.json()
    except:
        print("url: ", url, " cannot be processed")
        print(await resp.text())
        resp = {}
    return resp


async def async_get_resps(urls, queries = None, kwarg_list = None):
    if kwarg_list is None:
        kwarg_list = [{} for _ in queries] if isinstance(urls, str) else [{} for _ in urls]
    async with aiohttp.ClientSession() as session:
        tasks = []
        if isinstance(urls, str) and isinstance(queries, list):
            for i, query in enumerate(queries):
                tasks.append(fetch_resp(urls, query, session, **kwarg_list[i]))
        elif isinstance(urls, list):
            for i, url in enumerate(urls):
                tasks.append(fetch_resp(url, param=None, session=session, **kwarg_list[i]))
        else:
            raise ValueError("urls should be a list or a string")
        resps = await asyncio.gather(*tasks)
    return resps


def fetch_and_extract(url, saved_path):
    resp = requests.get(url, stream=True)
    content = resp.content
    zf = zipfile.ZipFile(BytesIO(content))
    with zf as f:
        f.extractall(saved_path)