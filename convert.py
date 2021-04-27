import hashlib
from pathlib import Path


def gethash(file):
    with open(file, 'rb') as f:
        data = f.read()
        return hashlib.blake2b(data).hexdigest()


root = Path("C:\\Jonah\\Wallpaper\\")
converted = root.joinpath("converted")
converted.mkdir(exist_ok=True)

seen = set()

images = list(root.glob("*.jpg"))
for img in images:
    # print(f"Converting {img.name}...")
    fhash = gethash(img)

    if(fhash in seen):
        print(f"Skipping {img.name}; already exists!")
        continue

    seen.add(fhash)
    newname = converted.joinpath(f"{fhash[:16]}.jpg")
    print(f"Renaming {img.name} to {newname}")

    img.rename(newname)
