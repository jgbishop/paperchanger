# Python Wallpaper Changer

This script makes it easy to change desktop wallpaper to a random file in a
given folder. It also provides support for grabbing new wallpaper images from
the Microsoft Windows lock screen wallpapers.

## Installation

1. Install all package requirements:
    * `pip install Pillow`
    * `pip install send2trash`
2. Place this script in a desired location.
3. Copy `config-template.json` to `config.json`.
4. Set the `sourceDir` path in the `config.json` file to the path of the folder
that contains your wallpaper image files.

## Usage

Simply issue `python chgpaper.py` to change the desktop wallpaper to a random
image.

## Options

The script accepts an _action_ parameter that may be one of the following
options:

**change**  
(Default action) Change the desktop wallpaper to a random file in the file pool.

**last**  
Display the filename of the previously set wallpaper, along with a time and date
stamp of when it was set.

**open**  
Open the `sourceDir` location in Windows Explorer.

**openlock**  
Open the lock screen content folder in Windows Explorer.

**remove**  
Moves the previously set wallpaper to the Recycle Bin.

**scan**  
Scan the lock screen content folder for new images.

**sync**  
Move staged images (after a successful `scan` operation) into the `sourceDir`
and add the files to the file pool.
