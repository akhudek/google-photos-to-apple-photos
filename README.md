# Google Photos Takeout to Apple Photos

This script imports an export of Google Photos to Apple Photos. It will
recreate albums checks for duplicates before importing. If it finds that
a photo is already uploaded, it will asssociate it with the correct album.

## Requirements

This requires python 3. 

## Usage

To use it, make the script executable and then give it the path to the
uncompressed Google Photos takeout folder (usually named `Takeout`).

## Warnings and Details

### Google Takeout

The takeout exported from Google must only contain Google Photos data. 
You can do this by going to [https://takeout.google.com](https://takeout.google.com), 
deselecting all, then selecting just Google Photos.
If you have a lot of photos it will create multiple zip files. *Do not
let Safari autmatically unzip these for you.* If you do, it will unzip
each one two a different Takeout folder (e.g. `Takeout`, `Takeout-2`, etc).
The zip files must all be uncompressed to the same folder to form a 
complete archive.

### Photos Import Errors
When running this script on my own photos, I found that after a while
the Photos app would start giving an error on import with reporting only
"Unknown Error." It appears there is some internal limit on the number
of calls to import after which it consistently fails. Restarting the 
Photos app fixes it. I'm not sure if importing in one big batch would help,
you could try importing all the photos first, then just running the 
script to associate the photos with albums.

### Skipping Already Imported Albums

The script will create a file called `migrate-progress.json` in the 
directory where you run it. Once it finishes with an album, it will
write folder path to this file. When runnign the script a subsequent
time it will skip any album whose path is in this file. This helps
save time if you need to rerun it due to errors. You can delete the
json if you want to run it from scratch.
