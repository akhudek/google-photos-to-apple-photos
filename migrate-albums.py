#!/usr/bin/env python3
# Copyright Alexander Hudek 2022

import sys
import os
import json
from subprocess import Popen, PIPE

ADD_PHOTO_TO_ALBUM_SCRIPT = """
    on unixDate(datetime)
        set command to "date -j -f '%A, %B %e, %Y at %I:%M:%S %p' '" & datetime & "'"
        set command to command & " +%s"
        
        set theUnixDate to do shell script command
        return theUnixDate
    end unixDate
    on run {albumName, image_path, image_filename, image_timestamp, image_size}
        tell application "Photos"
            if not (exists album named albumName) then
                make new album named albumName
            end if
            
            set images to search for image_filename
            repeat with img in images
                set myFilename to filename of img
                set myTimestamp to my unixDate(get date of img)
                set mySize to size of img                
                if image_filename is equal to myFilename and mySize is equal to (image_size as integer)
                    if image_timestamp is equal to "" or image_timestamp is equal to myTimestamp
                        set imgList to {img}
                        add imgList to album named albumName
                        return (get id of img)
                    end if
                end if
            end repeat

            set posixFile to (image_path as POSIX file)
            import posixFile into album named albumName with skip check duplicates
        end tell
        return ""
    end run
    """

ADD_PHOTO_SCRIPT = """
    on unixDate(datetime)
        set command to "date -j -f '%A, %B %e, %Y at %I:%M:%S %p' '" & datetime & "'"
        set command to command & " +%s"
        
        set theUnixDate to do shell script command
        return theUnixDate
    end unixDate
    on run {image_path, image_filename, image_timestamp, image_size}
        tell application "Photos"
            set images to search for image_filename
            repeat with img in images
                set myFilename to filename of img
                set myTimestamp to my unixDate(get date of img)
                set mySize to size of img                
                if image_filename is equal to myFilename and mySize is equal to (image_size as integer)
                    if image_timestamp is equal to "" or image_timestamp is equal to myTimestamp
                        return (get id of img)
                    end if
                end if
            end repeat

            set posixFile to (image_path as POSIX file)
            import posixFile with skip check duplicates
        end tell
        return ""
    end run
    """

LOG_FILE = "migrate-progress.json"
processed_albums = {}

if len(sys.argv) < 1:
    print("migrate-albums.py [takeout-directory]")
    exit(1)


def load_progress():
    with open(LOG_FILE) as json_file:
        return json.load(json_file)


def save_progress():
    j = json.dumps(processed_albums, indent=2)
    with open(LOG_FILE, "w") as f:
        f.write(j)


if os.path.isfile(LOG_FILE):
    processed_albums = load_progress()


def photo_timestamp(photo_path):
    try:
        with open(photo_path + ".json") as json_file:
            data = json.load(json_file)
            return data["photoTakenTime"]["timestamp"]
    except FileNotFoundError:
        return ""


def album_metadata(directory):
    for path, dirs, files in os.walk(directory):
        for f in files:
            if f == "metadata.json":
                with open(os.path.join(path, f)) as json_file:
                    data = json.load(json_file)
                    yield [path, data["title"]]


def album_photos(directory):
    for path, dirs, files in os.walk(directory):
        for f in files:
            if not f.endswith(".json"):
                yield [os.path.join(path, f), f]


def add_photo_to_album(album_name, image_path, image_filename, taken_ts):
    print(f"Adding {image_filename} {taken_ts} to {album_name}")
    image_size = os.path.getsize(image_path)
    args = [album_name, image_path, image_filename, taken_ts, str(image_size)]
    p = Popen(["osascript", "-"] + args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate(ADD_PHOTO_TO_ALBUM_SCRIPT.encode("utf-8"))
    return stdout.decode("utf-8").rstrip()


def add_photo(image_path, image_filename, taken_ts):
    print(f"Adding {image_filename} {taken_ts}")
    image_size = os.path.getsize(image_path)
    args = [image_path, image_filename, taken_ts, str(image_size)]
    p = Popen(["osascript", "-"] + args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate(ADD_PHOTO_SCRIPT.encode("utf-8"))
    return stdout.decode("utf-8").rstrip()


def photos(directory):
    for path, dirs, files in os.walk(directory):
        for f in files:
            if not f.endswith(".json"):
                yield [path, f]


for album_folder, album_name in album_metadata(sys.argv[1]):
    print(f"Processing {album_name}")
    if album_folder not in processed_albums:
        for image_path, image_filename in album_photos(album_folder):
            image_timestamp = photo_timestamp(image_path)
            id = add_photo_to_album(
                album_name, image_path, image_filename, image_timestamp
            )
            if not id == "":
                print(f"Added {id} to {album_name}")
            else:
                print(f"Imported {image_filename} to {album_name}")
        processed_albums[album_folder] = True
        save_progress()
    else:
        print(f"Skipping album {album_folder}")


for folder, image_file in photos(sys.argv[1]):
    if (
        folder not in processed_albums
        and image_file != ".DS_Store"
        and image_file != "archive_browser.html"
    ):
        image_path = os.path.join(folder, image_file)
        image_timestamp = photo_timestamp(image_path)
        id = add_photo(image_path, image_file, image_timestamp)
        if not id == "":
            print("Skipped as it already exists")
        else:
            print(f"Imported {image_file}")
