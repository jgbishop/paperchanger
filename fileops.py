import ctypes
import hashlib
import json
import os
from collections import UserDict
from datetime import datetime
from pathlib import Path
from shutil import copyfile

from PIL import Image
from send2trash import send2trash


USERHOME = Path('~').expanduser()
SPI_SETDESKWALLPAPER = 20
SPI_UPDATEINIFILE = 1

LOCKSCREEN_PATH = (USERHOME / "AppData" / "Local" / "Packages"
                   / "Microsoft.Windows.ContentDeliveryManager_cw5n1h2txyewy"
                   / "LocalState" / "Assets")


class ConfigFile(UserDict):
    def __init__(self, path):
        self.path = path

        try:
            with Path(self.path).open() as file:
                self.data = json.loads(file.read())
        except FileNotFoundError:
            raise

    def save(self):
        with Path(self.path).open('w') as file:
            file.write(json.dumps(self.data, indent=2))


def browse_lockdir():
    os.startfile(LOCKSCREEN_PATH)


def change_paper(filepath):
    # Taken from https://stackoverflow.com/a/44406182/1128047
    retval = (ctypes.WinDLL('user32', use_last_error=True)
              .SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, str(filepath),
                                     SPI_UPDATEINIFILE))

    if not retval:
        raise ctypes.WinError(ctypes.get_last_error())


def create_filename(filehash):
    return f"{filehash[:16]}.jpg"


def datetime_to_string(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def find_files(folder):
    """
    Finds image files in the given folder, returning them as a list.
    """
    files = set()
    for f in os.listdir(folder):
        filepath = Path(folder) / f
        if (filepath.is_file() and f.lower().endswith('.jpg')):
            files.add(f)

    return files


def get_filehash(file):
    with Path(file).open('rb') as fh:
        data = fh.read()
        return hashlib.blake2b(data).hexdigest()


def move_staging_files(config):
    source_dir = config.get('sourceDir')
    staging = Path(source_dir) / 'staging'
    file_pool = config.get('filePool', {})

    for f in os.listdir(staging):
        filepath = Path(staging) / f
        if (not filepath.is_file() or not f.lower().endswith('.jpg')):
            continue

        print(f" - Moving {f}")
        try:
            newpath = Path(source_dir) / f
            filepath.rename(newpath)
        except FileExistsError:
            filepath.unlink(missing_ok=True)

        file_pool.setdefault(f, {'consumed': False, 'lastShown': None})


def recycle_file(config, filename):
    print(f"Removing {filename}...")
    source_dir = config.get('sourceDir')
    file_pool = config.get('filePool', {})

    filepath = Path(source_dir) / filename
    if filepath.is_file():
        try:
            send2trash(filepath)
            file_pool.pop(filename, None)
        except Exception:
            raise


def scan_lockscreen_folder(config):
    staging = Path(config.get('sourceDir')) / 'staging'

    # Create the staging directory if it doesn't exist
    if not staging.exists():
        staging.mkdir()

    has_candidate = False
    for f in os.scandir(LOCKSCREEN_PATH):
        if not f.is_file():
            continue

        # Only examine files larger than 100 KB, which are likely to be the
        # images we're interested in.
        size = Path(f.path).stat().st_size
        if size < (1024 * 100):
            continue

        with Image.open(f.path) as img:
            width, height = img.size

            if width < height:
                continue  # Skip portrait images

            filename = create_filename(get_filehash(f))
            if filename in config.get('filePool', {}):
                continue

            print(f" - Found candidate image of size {size}: {f.name[:16]}")
            print(f"   Dimensions: {width} x {height}")

            has_candidate = True
            copyfile(f.path, Path(staging) / filename)

    # Open Windows Explorer to the staging location
    if has_candidate:
        os.startfile(staging)
    else:
        print(" - No candidates found")


def string_to_datetime(string):
    try:
        return datetime.strptime(string, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise


def validate_config(config):
    files = find_files(config.get('sourceDir'))
    file_pool = config.get('filePool', {})
    current = set(file_pool.keys())
    on_disk = set(files)

    print(f" - Found {len(on_disk)} files on disk")
    print(f" - Have {len(current)} files in config")

    to_add = [x for x in on_disk if x not in current]
    to_del = [x for x in current if x not in on_disk]

    if (to_del):
        print(f" - {len(to_del)} files to remove")
        for x in to_del:
            file_pool.pop(x, None)

    if (to_add):
        print(f" - {len(to_add)} files to add")
        for x in to_add:
            file_pool.setdefault(x, {'consumed': False, 'lastShown': None})
