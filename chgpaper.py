import argparse
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from random import randrange

from fileops import (
    ConfigFile, browse_lockdir, change_paper, datetime_to_string,
    move_staging_files, recycle_file, scan_lockscreen_folder,
    string_to_datetime, validate_config)


script_dir = Path(os.path.realpath(__file__)).parent

choices = ['change', 'last', 'open', 'openlock', 'remove', 'scan', 'sync']
parser = argparse.ArgumentParser(description="Changes the desktop wallpaper.")
parser.add_argument('action', choices=choices, default='change', nargs='?')

args = parser.parse_args()
cfg_path = script_dir / 'config.json'

if args.action == 'openlock':
    print("Opening lock screen image source folder")
    browse_lockdir()
    sys.exit(0)

if not cfg_path.is_file():
    template_path = script_dir / "config-template.json"
    shutil.copyfile(template_path, cfg_path)
    print("No config file found; created one from template.")
    print("Make sure to set the source folder before running again!")
    sys.exit(0)

try:
    config = ConfigFile(cfg_path)
    file_pool = config.get('filePool', {})
    previous_file = config.get('previousFile', '')
except FileNotFoundError:
    print(f"ERROR: Unable to locate config file: {cfg_path}")
    sys.exit(1)

if args.action == 'last':
    if previous_file:
        print(f"Previous file: {previous_file}")
        last_shown = file_pool.get(previous_file, {}).get('lastShown')
        last_shown = last_shown if last_shown else 'Never'
        print(f"Set on: {last_shown}")
    else:
        print("No previous file found!")

    sys.exit(0)

if args.action == 'open':
    print("Opening stored wallpapers folder")
    os.startfile(config.get('sourceDir'))
    sys.exit(0)

if args.action == 'remove':
    if previous_file:
        recycle_file(previous_file)
        config.save()
    else:
        print("No previous file found to remove!")

    sys.exit(0)

if args.action == 'scan':
    print("Scanning for lock screen images")
    scan_lockscreen_folder(config)
    sys.exit(0)

if args.action == 'sync':
    print("Syncing staged images to source directory")
    move_staging_files(config)
    config.save()
    sys.exit(0)

print("Validating config file")
validate_config(config)

available = [key for key, store in file_pool.items()
             if not store.get('consumed', False)]

print(f"Files left in the pool: {len(available)}")

if not available:
    print(" - Refilling the pool!")
    for store in file_pool.values():
        store['consumed'] = False

    available = list(file_pool.keys())

random_filename = available[randrange(0, len(available))]
selected_file = Path(config.get('sourceDir')) / random_filename
pool_entry = file_pool.get(random_filename, {})

delta = 0
now = datetime.now()
last_shown = pool_entry.get('lastShown', None)
if last_shown:
    then = string_to_datetime(last_shown)
    delta = now - then

last_shown = f"{delta.days} day(s) ago" if delta else "Never"
print(f"\nChanging wallpaper to: {random_filename} (Last Shown: {last_shown})")
change_paper(selected_file)

pool_entry['consumed'] = True
pool_entry['lastShown'] = datetime_to_string(now)
config['previousFile'] = random_filename
config.save()
