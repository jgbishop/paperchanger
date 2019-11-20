# Python Wallpaper Changer

This script makes it easy to change desktop wallpaper to a random file in a given
folder. It also provides support for grabbing new wallpaper images from the
Microsoft Windows lock screen wallpapers.

## Installation

1. Install the Pillow python package: `pip install Pillow`
2. Place this script in a desired location.
3. In that same location, create a folder in which to store your wallpaper images,
noting the path to this target location.
4. Issue the following command, passing the target location above in as the
`<target>` parameter, to create a new configuration file:
`python paperchanger.py --create <target>`

## Usage

Simply issue `python paperchanger.py` to change the desktop wallpaper to a random
image.

## Options

The following command line options are available:

**`{config_file}`**  
The first positional argument is the name of the configuration file to read. If
not specified, the default filename **paper_changer.cfg** will be read in.

**`--create <target>`**  
Create a new configuration file, using the specified target folder as the
repository of files.

**`--lockbrowse`**  
Open the Microsoft Windows lock screen image storage location in a Windows
Explorer window.

**`--lockscan`**  
Scan the Microsoft Windows lock screen image storage location for new images. If
any new images are found, the location is opened in a Windows Explorer window
for you to preview the images.

**`--locksync`**  
Move the images found by the `--lockscan` option to the file repository, adding
them to the available image pool.

**`--pool`**  
Show the current random selection pool.

**`--sync`**  
Synchronize the configuration file with the image pool, adding any new files
that were found, and removing any files that are no longer present.
