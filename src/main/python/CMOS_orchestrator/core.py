import glob
import logging
import os
import platform
import shutil
import sys
import uuid
from collections import namedtuple
import json
import subprocess
from typing import List, Tuple

logger = logging.getLogger("cmos")

def get_top_level_device(device):
    logger.info(device)
    top_devices = subprocess.check_output(['lsblk', '-no', 'pkname', device], universal_newlines=True).strip()
    top_devices = set(top_devices.split('\n'))
    assert len(top_devices) <= 1, "More than one top-level device found!"
    top_device = top_devices.pop()

    # Checking if top_device is empty
    if top_device == '':
        logger.info("empty string found")
        logger.info(f'The top-level device for {device} is: {device}')
        return device
    else:
        top_device = '/dev/' + top_device
        logger.info(f'The top-level device for {device} is: {top_device}')
        return top_device


# Define the named tuple outside the function
BlockDevice = namedtuple('BlockDevice', 'name, rm, mountpoint')


def get_block_devices() -> List[BlockDevice]:
    """
    Get a list of all block devices.
    """
    commanded = subprocess.run(['lsblk', '-lpJ', '-o', 'NAME,RM,MOUNTPOINT'],
                               capture_output=True, text=True, check=True)
    output = commanded.stdout
    data = json.loads(output)

    # Convert dictionaries to named tuples
    block_devices = [BlockDevice(**device) for device in data['blockdevices']]

    return block_devices


def create_directory_and_mount(possible_mount):
    uuid4 = str(uuid.uuid4())
    path_to_mount = "/mount_{0}_{1}".format(possible_mount, uuid4)

    # Mimic echo command
    logger.info("Creating the following directory and attempting to mount to it.")
    logger.info(path_to_mount)

    # Mimic mkdir -p command
    os.makedirs(path_to_mount, exist_ok=True)

    # Attempt to mount device
    mount_command = "sudo mount {0} {1}".format(possible_mount, path_to_mount)
    os.system(mount_command)
    return path_to_mount


def check_root_files(path_to_mount: str, file_lists: List[Tuple[str, ...]]) -> bool:
    files_in_directory = [file for file in os.listdir(path_to_mount)
                          if not ('.iso' in file or '.part' in file)]

    for file_list in file_lists:
        if set(files_in_directory) == set(file_list):
            return True
    return False


def check_block_devices() -> BlockDevice:
    base_file_list = ("boot", "EFI", "live", "syslinux")
    file_lists = [
        base_file_list,
        base_file_list + ("autorun.ico", "autorun.inf", "syslinux.cfg", "System Volume Information"),
        base_file_list + ("System Volume Information",),
    ]

    block_devices = get_block_devices()
    for block_device in block_devices:
        path_to_mount = create_directory_and_mount(block_device.name)
        if check_root_files(path_to_mount, file_lists):
            logger.info(
                f"The contents of the root directory of the device {block_device.name} match with one of the target file lists")
            correct_block_device = [bd for bd in get_block_devices() if bd.mountpoint == path_to_mount][0]
            return correct_block_device

    raise Exception('No block device matched the given file lists.')


def gather_and_extract_iso_files(root_path: str):
    iso_path = "/iso"

    # Equivalent to mkdir -p
    os.makedirs(iso_path, exist_ok=True)

    # find and copy .iso files
    for file in os.listdir(root_path):
        if file.endswith('.iso'):
            shutil.copy(os.path.join(root_path, file), iso_path)

    # find and extract .001 files
    # for file in os.listdir(root_path):
    #     if file.endswith('.001'):
    #         subprocess.run(['7z', 'x', os.path.join(root_path, file), f'-o{iso_path}'])

    # Find and concatenate .part* files
    concatenated_iso_path = os.path.join(iso_path, 'concatenated_iso.iso')
    part_files_found = False

    for i in range(1, 21):
        for file in os.listdir(root_path):
            if file.endswith(f'.part{i}') and not file.startswith("._"):
                part_files_found = True
                logger.info(f"Adding the following file to the ISO: {os.path.join(root_path, file)}")
                with open(os.path.join(root_path, file), 'rb') as pf:
                    with open(concatenated_iso_path, 'ab') as cif:
                        shutil.copyfileobj(pf, cif)
                break
        if not part_files_found:
            logger.info("No more part files found, finished concatenation.")
            break
        part_files_found = False


class MultipleFilesError(Exception):
    pass


def verify_iso_file():
    iso_path = "/iso"
    iso_files = glob.glob(os.path.join(iso_path, "*.iso"))

    if not iso_files:
        raise FileNotFoundError("We expected at least one ISO file. Make sure to copy an ISO file onto your USB.")
    elif len(iso_files) > 1:
        msg = ["Too many ISO files given."]
        msg.append(f"Files in {iso_path} directory:")
        msg += iso_files
        raise MultipleFilesError('\n'.join(msg))
    else:
        logger.info(f"ISO file in {iso_path} directory: {iso_files[0]}")
        return iso_files[0]



def main():
    if platform.system() == 'Windows':
        logger.info("You are currently running Windows. CMOS only supports X86-64 Linux based operating systems.")
        return
    cmos_usb = check_block_devices()
    gather_and_extract_iso_files(cmos_usb.mountpoint)
    iso_file = verify_iso_file()
    top_level_device = get_top_level_device(cmos_usb.name)
    cmd = ['woeusb', '--target-filesystem', 'NTFS', '--device', iso_file, top_level_device]
    subprocess.run(cmd, check=True)
