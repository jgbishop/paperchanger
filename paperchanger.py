import argparse
import ctypes
import json
import os
import sys

from random import randrange
from shutil import copyfile

from PIL import Image


USERHOME = os.path.expanduser("~")
LOCKSCREEN_PATH = os.path.join(USERHOME, "AppData", "Local", "Packages",
                               "Microsoft.Windows.ContentDeliveryManager_cw5n1h2txyewy",
                               "LocalState", "Assets")


class ConfigData:
    def __init__(self, path):
        self.cfg_path = path
        self.data = {
            'CONFIG_VERSION': 1,
            'files': {},
            'lock_screen_pool': [],
            'previous': '',
            'target': '',
        }

    def get(self, key, default=None):
        return self.data.get(key, default)

    def load(self):
        try:
            with open(self.cfg_path, 'r') as f:
                self.data = json.loads(f.read())

            if('CONFIG_VERSION' in self.data):
                return True
            else:
                print("ERROR: Invalid configuration file!")
                return False

        except FileNotFoundError:
            print(f"ERROR: Unable to locate config file: {cfg_path}")
            print("\nCreate a config file with the --create {target} option")
            return False

    def save(self):
        with open(self.cfg_path, 'w') as f:
            f.write(json.dumps(self.data))

    def set(self, key, value):
        self.data[key] = value
        return self.data[key]


def find_files(folder):
    """
    Finds image files in the given folder, returning them as a list.
    """
    files = set()
    for f in os.listdir(folder):
        if(os.path.isfile(os.path.join(folder, f)) and
           f.lower().endswith(".jpg")):
            files.add(f)

    return files


def find_lockscreen_files(cfg):
    print("Scanning for lock screen images...")
    staging = os.path.join(cfg.get('target'), 'staging')

    # Create the staging directory if it doesn't exist
    if(not os.path.exists(staging)):
        os.mkdir(staging)

    lspool = cfg.get('lock_screen_pool', [])
    lspool_set = set(lspool)

    for f in os.scandir(LOCKSCREEN_PATH):
        if(not f.is_file()):
            continue

        # Only examine files larger than 100 KB, which are likely to be the images
        # we're interested in.
        size = os.path.getsize(f.path)
        if(size < (1024 * 100)):
            continue

        with Image.open(f.path) as img:
            width, height = img.size

            if(width < height):
                continue

            print(f" - Found candidate image of size {size}: {f.name}")
            print(f"   Dimensions: {width} x {height}")

            if(f.name in lspool_set):
                print("   Skipping (already parsed)")
                continue

            lspool.append(f.name)
            short_hash = f.name[:16]

            copyfile(f.path, os.path.join(staging, f"lock_screen_{short_hash}.jpg"))

    # Open Windows Explorer to the staging location
    os.startfile(staging)


def move_staging_files(cfg):
    print("Syncing staged lock screen images to target directory...")

    target = cfg.get('target')
    staging = os.path.join(target, 'staging')

    papers = cfg.get('files', {})

    # files = set()
    for f in os.listdir(staging):
        if(os.path.isfile(os.path.join(staging, f)) and f.lower().endswith('.jpg')):
            print(f" - Moving {f}")
            try:
                os.rename(os.path.join(staging, f), os.path.join(target, f))
            except FileExistsError:
                os.remove(os.path.join(staging, f))

            papers.setdefault(f, True)


script_dir = os.path.dirname(os.path.realpath(__file__))

parser = argparse.ArgumentParser(description="Changes the desktop wallpaper.")
parser.add_argument('config_file', default="paper_changer.cfg", nargs="?")
parser.add_argument('--create', help="Create a new config file; pass in the target dir to use")
parser.add_argument('--lockbrowse', action="store_true", help="Open the lock screen source folder")
parser.add_argument('--lockscan', action="store_true",
                    help="Scan for Microsoft lock screen images")
parser.add_argument('--locksync', action='store_true',
                    help="Sync lock screen images from staging directory")
parser.add_argument('--pool', action='store_true', help="Show files in the selection pool.")
parser.add_argument('--sync', action="store_true",
                    help="Keep the config file in sync with the target directory.")

args = parser.parse_args()
cfg_path = os.path.join(script_dir, args.config_file)

print(f"Loading configuration file: {cfg_path}")
cfg = ConfigData(cfg_path)

if(args.create):
    if(os.path.isfile(cfg_path)):
        print(f"ERROR: Config file '{cfg_path}' already exists.")
        sys.exit(1)

    cfg.set('target', args.create)

    print(f"Creating new config file: {cfg_path}")
    print(" - Loading files from target directory")
    files = find_files(cfg.get('target'))
    print(f" - Files found: {len(files)}")

    cfg_files = cfg.get('files', {})
    for f in files:
        cfg_files.setdefault(f, True)

    cfg.save()
    print(" - Config file created; exiting!")
    sys.exit(0)

if(args.lockbrowse):
    print("Opening lock screen image source folder")
    os.startfile(LOCKSCREEN_PATH)
    sys.exit(0)

if(not cfg.load()):
    print("Unable to load config file; exiting!")
    sys.exit(1)

# Gather a list of all the wallpapers in the selection pool
papers = cfg.get('files', {})

if(args.lockscan):
    find_lockscreen_files(cfg)
    cfg.save()
    print("Lock screen files parsed; exiting!")
    sys.exit(0)

if(args.locksync):
    move_staging_files(cfg)
    cfg.save()
    print("Lock screen files moved; exiting!")
    sys.exit(0)

if(args.sync):
    print("Syncing config file")

    files = find_files(cfg.get('target'))
    current = set(papers.keys())
    on_disk = set(files)

    print(f" - Found {len(on_disk)} files on disk")
    print(f" - Have {len(current)} files in config")

    to_add = [x for x in on_disk if x not in current]
    to_del = [x for x in current if x not in on_disk]

    print(f" - {len(to_add)} files to add")
    print(f" - {len(to_del)} files to remove")

    # First, remove the files that are no longer on disk
    for x in to_del:
        papers.pop(x, None)

    # Now add the new ones
    for x in to_add:
        papers.setdefault(x, True)

    cfg.save()

    print(" - Sync completed; exiting!")
    sys.exit(0)

pool = [x for x in papers if papers[x]]
if(not pool):
    # Refill the pool if it's empty
    for x in papers:
        papers[x] = True

    pool = list(papers.keys())

if(args.pool):
    print(f"Files in the selection pool: {len(pool)}")
    for x in sorted(pool):
        print(f"  {x}")
    sys.exit(0)

# Select a random item from the list
random_filename = pool[randrange(0, len(pool))]

# Change the wallpaper
paper_file = os.path.join(cfg.get("target"), random_filename)
print(f"Changing wallpaper to {random_filename}")

SPI_SETDESKWALLPAPER = 20
SPI_UPDATEINIFILE = 1  # Taken from https://stackoverflow.com/a/44406182/1128047
retval = (ctypes.WinDLL('user32', use_last_error=True)
          .SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, paper_file, SPI_UPDATEINIFILE))

if(not retval):
    raise ctypes.WinError(ctypes.get_last_error())

# Update the config file
papers[random_filename] = False
cfg.set('previous', random_filename)
cfg.save()
