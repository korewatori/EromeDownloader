import argparse
import sys
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import tldextract
from tqdm import tqdm

COLOR_RED = "\x1b[38;5;1m"
COLOR_GREEN = "\x1b[32m"
COLOR_YELLOW = "\x1b[38;5;3m"
COLOR_END = "\033[0m"

session = requests.Session()

def collect_links(album_url):
    parsed_url = urlparse(album_url)
    if parsed_url.hostname != "www.erome.com":
        raise Exception(f"Host must be www.erome.com")

    r = session.get(album_url, headers={"User-Agent": "Mozilla/5.0"})
    if r.status_code != 200:
        raise Exception(f"HTTP error {r.status_code}")

    soup = BeautifulSoup(r.content, "html.parser")
    title = soup.find("meta", property="og:title")["content"]
    videos = [video_source["src"] for video_source in soup.find_all("source")]
    images = [
        image["data-src"] for image in soup.find_all("img", {"class": "img-back"})
    ]
    urls = list(set([*videos, *images]))
    download_path = get_final_path(title)
    existing_files = get_files_in_dir(download_path)

    print(f"Downloading files from album: {album_url}")
    print(f"Title: {title}")
    print(f"Total Files: {len(urls)}")
    # Uncomment the lines below if you want the list of files to be printed to the console.
    # print("Files to be downloaded:")
    # for file_url in urls:
    #    print(file_url + COLOR_END)
    print("\nStarting Download...\n")

    files_complete = 0
    files_skipped = 0
    files_failed = 0

    for file_url in urls:
        result = download(file_url, download_path, album_url, existing_files)
        if result == "downloaded":
            files_complete += 1
        elif result == "skipped":
            files_skipped += 1
        elif result == "failed":
            files_failed += 1

    clear_console()
    print(
    f"{COLOR_GREEN}| Files Complete: {files_complete} {COLOR_YELLOW}- Files Skipped: {files_skipped} {COLOR_RED}- Files Failed: {files_failed} {COLOR_END}|\n"
    )
    print(f'Finished Downloading {album_url}. Enjoy :)')


def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')


def get_final_path(title):
    final_path = os.path.join("downloads", title)
    if not os.path.isdir(final_path):
        os.makedirs(final_path)
    return final_path


def get_files_in_dir(directory):
    return [
        f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))
    ]


def download(url, download_path, album=None, existing_files=[]):
    parsed_url = urlparse(url)
    file_name = os.path.basename(parsed_url.path)
    if file_name in existing_files:
        print(COLOR_YELLOW + f'[#] Skipping "{url}" [already downloaded]' + COLOR_END)
        return "skipped"

    extracted = tldextract.extract(url)
    hostname = "{}.{}".format(extracted.domain, extracted.suffix)
    with session.get(
        url,
        headers={
            "Referer": f"https://{hostname}" if album is None else album,
            "Origin": f"https://{hostname}",
            "User-Agent": "Mozilla/5.0",
        },
        stream=True,
    ) as r:
        if r.ok:
            file_path = os.path.join(download_path, file_name)
            total_size = int(r.headers.get("content-length", 0))
            progress = tqdm(total=total_size, unit="B", unit_scale=True)
            with open(file_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        progress.update(len(chunk))
            progress.close()
            print(f'[#] Downloaded "{url}"' + COLOR_END)
        else:
            print(COLOR_RED + str(r))
            print(COLOR_RED + f'[-] Failed to Download "{url}"' + COLOR_END)
            return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(sys.argv[1:])
    parser.add_argument("-u", help="url to download", type=str, required=True)
    args = parser.parse_args()
    collect_links(args.u)
