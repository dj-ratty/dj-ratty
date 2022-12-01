import os
import json
import urllib.request
from dataclasses import dataclass

ORIGINAL_URL = "https://raw.githubusercontent.com/dj-ratty/beau-redirect/master/parts/en.json"
TRANSLATE_RU_URL = "https://raw.githubusercontent.com/dj-ratty/beau-redirect/master/parts/ru.json"
BASE_URL = "https://quickchart.io/chart?bkg=transparent&f=png&w={width}&h={height}&c={chart}"
ROOT_DIR = os.path.dirname(__file__)
JSON_PATH = os.path.join(ROOT_DIR, "stats.json")
IMG_DIR = os.path.join(ROOT_DIR, "out")
FORCE_UPDATE_IMG_STR = str(os.environ.get("BEAUFORCEUPDATEIMG", "0"))

def get_force_update_img():
    return FORCE_UPDATE_IMG_STR.lower() in ("1", "true", "y", "yes")

@dataclass
class Chart:
    type: str
    sizes: tuple

    def generate_urls(self, data: dict):
        data["type"] = self.type
        return tuple([(BASE_URL.format(width=width, height=height, chart=data), (width, height)) for width, height in self.sizes])


Radial = Chart(type="radialGauge", sizes=((64, 64), (128, 128), (256, 256)))
Bar = Chart(type="progressBar", sizes=((64, 16), (128, 32), (256, 64), (256, 32)))


def get_json_from_url(url):
    with urllib.request.urlopen(url) as res:
        return json.loads(res.read().decode(res.headers.get_content_charset("utf-8")))


def save_img_from_url(url, filename):
    url = url.replace(" ", "%20")
    urllib.request.urlretrieve(url, filename)


def get_int_percent_from_dict_lens(a, b):
    if len(a) < len(b):
        a, b = b, a
    return int((len(b) / len(a)) * 100)


def get_lens_from_json():
    if not os.path.exists(JSON_PATH):
        return False
    with open(JSON_PATH, mode="r") as f:
        data = json.load(f)
    return data


def save_lens_to_json(original, translate_ru, not_save=False):
    data = {"buggachat": len(original), "translate_ru": {"percent": get_int_percent_from_dict_lens(original, translate_ru), "count": len(translate_ru)}}
    if not_save:
        return data
    with open(JSON_PATH, mode="w+") as f:
        json.dump(data, f, indent=4)
    return data


def main():
    old = get_lens_from_json()
    
    orig_urls = get_json_from_url(ORIGINAL_URL)
    russ_urls = get_json_from_url(TRANSLATE_RU_URL)

    if old != False:
        new = save_lens_to_json(orig_urls, russ_urls, not_save=True)
        if old["translate_ru"]["percent"] == new["translate_ru"]["percent"] and get_force_update_img() != True:
            if old != new:
                save_lens_to_json(orig_urls, russ_urls)
            return
        save_lens_to_json(orig_urls, russ_urls)
    else:
        new = save_lens_to_json(orig_urls, russ_urls)
    
    if not os.path.exists(IMG_DIR):
        os.makedirs(IMG_DIR)

    data = {"data": {"datasets": [{"backgroundColor": "%23C74ABB", "label": "Ru Translated", "data": [new["translate_ru"]["percent"]]}]}}
    for chart_type in (Radial, Bar):
        urls_sizes = chart_type.generate_urls(data)
        for img_url, img_size in urls_sizes:
            filename = chart_type.type + f"_{'x'.join(tuple(map(str, img_size)))}" + ".png"
            save_img_from_url(img_url, os.path.join(IMG_DIR, filename))


if __name__ == "__main__":
    main()
