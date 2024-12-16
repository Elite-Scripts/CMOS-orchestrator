import glob
import json
import logging
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import uuid
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Tuple

import WoeUSB
from WoeUSB.core import init

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


def unmount_directory(fullpath_to_mount: str):
    logger.info("Attempting to unmount: %s", fullpath_to_mount)

    unmount_command = ["umount", fullpath_to_mount]
    try:
        subprocess.run(unmount_command, check=True, capture_output=True, text=True)
        logger.info("Successfully unmounted: %s", fullpath_to_mount)
    except subprocess.CalledProcessError as e:
        logger.error("Error during the unmount command:")
        logger.error(e.stderr)


def create_directory_and_mount(device_mount_directory_path: str, possible_mount):
    uuid4 = str(uuid.uuid4())
    path_to_mount = "mount_{0}_{1}".format(possible_mount, uuid4)
    fullpath_to_mount = os.path.join(device_mount_directory_path, path_to_mount)

    # Mimic echo command
    logger.info("Creating the following directory and attempting to mount to it.")
    logger.info(fullpath_to_mount)

    # Mimic mkdir -p command
    os.makedirs(fullpath_to_mount, exist_ok=True)

    # Attempt to mount device
    mount_command = ["mount", possible_mount, fullpath_to_mount]
    try:
        subprocess.run(mount_command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.error("Error during the mount command:")
        logger.error(e.stderr)

    return fullpath_to_mount


def check_root_files(path_to_mount: str, file_lists: List[Tuple[str, ...]]) -> bool:
    files_in_directory = [file for file in os.listdir(path_to_mount)
                          if not ('.iso' in file or '.part' in file or 'recycle' in file.lower())]

    for file_list in file_lists:
        if set(files_in_directory) == set(file_list):
            return True
    return False


def check_block_devices(device_mount_directory_path:str) -> BlockDevice:
    base_file_list = ("boot", "EFI", "live", "syslinux", "CMOS")
    file_lists = [
        base_file_list,
        # Rufus
        base_file_list + ("syslinux.cfg", "System Volume Information"),
        # Rufus with extended label and icons
        base_file_list + ("autorun.ico", "autorun.inf", "syslinux.cfg", "System Volume Information"),
        base_file_list + ("autorun.ico", "autorun.inf", "System Volume Information"),
        base_file_list + ("System Volume Information",),
    ]

    block_devices = get_block_devices()
    for block_device in block_devices:
        path_to_mount = create_directory_and_mount(device_mount_directory_path, block_device.name)
        contents = os.listdir(path_to_mount)
        logger.info(f"Mounting {path_to_mount} with the following contents: {', '.join(contents)}")
        if check_root_files(path_to_mount, file_lists):
            logger.info(
                f"The contents of the root directory of the device {block_device.name} match with one of the target file lists")
            correct_block_device = [bd for bd in get_block_devices() if bd.mountpoint == path_to_mount][0]
            return correct_block_device

    raise Exception('No block device matched the given file lists.')


def copy_with_progress(src_path, dst_path, progress_callback=lambda file_path, copied_bytes, progress: None, chunk_size_kb=1000):
    file_size = os.path.getsize(src_path)
    chunk_size = chunk_size_kb * 1024  # convert from Kilobytes to bytes
    copied_bytes = 0
    with open(src_path, 'rb') as src_file, open(dst_path, 'ab') as dst_file:
        for chunk in iter(lambda: src_file.read(chunk_size), b''):
            dst_file.write(chunk)
            copied_bytes += len(chunk)
            copy_progress = copied_bytes / file_size
            progress_callback(src_path, copied_bytes, copy_progress)


@dataclass
class ProgressUpdate:
    file_path: str
    progress_percent: int


class PartsProgressReporter:
    def __init__(self, total_bytes, observers=None):
        self.total_bytes = total_bytes
        self.last_reported_percent = None
        self.file_bytes_copied = {}
        if observers is None:
            observers = []
        self.observers = observers

    def attach(self, observer):
        self.observers.append(observer)

    def notify_observers(self, file_path, last_reported_percent):
        progress_update = ProgressUpdate(file_path, last_reported_percent)
        for observer in self.observers:
            observer.update_progress(progress_update)

    def notify_observers_process_completed(self):
        for observer in self.observers:
            observer.process_completed()

    def report_progress(self, file_path, copied_bytes, progress):
        self.file_bytes_copied[file_path] = copied_bytes
        overall_part_copying_progress = sum(self.file_bytes_copied.values()) / self.total_bytes
        progress_percent = round(overall_part_copying_progress * 100)
        if self.last_reported_percent != progress_percent:
            self.last_reported_percent = progress_percent
            logger.debug(f"Total copy progress: {progress_percent}%")
            self.notify_observers(file_path, progress_percent)



def calculate_total_size_of_files(file_paths: list):
    total_size = 0
    for file_path in file_paths:
        if os.path.isfile(file_path):
            total_size += os.path.getsize(file_path)
    return total_size


def bytes_to_mb(bytes):
    return bytes / 1048576


def gather_and_extract_iso_files(root_path: str, root_mount_path_directory: str, gather_iso_observers: list):
    iso_path = root_mount_path_directory

    # Equivalent to mkdir -p
    logger.info("Using the following root mount path directory: " + root_mount_path_directory)
    os.makedirs(iso_path, exist_ok=True)

    # find and copy .iso files
    for file in os.listdir(root_path):
        if file.endswith('.iso'):
            shutil.copy(os.path.join(root_path, file), iso_path)

    # Find and concatenate .part* files
    concatenated_iso_path = os.path.join(iso_path, 'concatenated_iso.iso')
    part_file_regex = r'^[^_.].*\.part\d+$'
    part_files = [os.path.join(root_path, file) for file in os.listdir(root_path) if re.match(part_file_regex, file)]
    if part_files:
        # Use regex to extract the part number from the filename, convert to int for sorting
        part_files.sort(key=lambda file: int(re.search(r'part(\d+)', file).group(1)))
        combined_part_file_sizes = calculate_total_size_of_files(part_files)
        combined_part_file_sizes_mb = bytes_to_mb(combined_part_file_sizes)
        logger.info(f"Attempting to combine {len(part_files)} part files that total {combined_part_file_sizes_mb} MB")
        parts_progress_reporter = PartsProgressReporter(combined_part_file_sizes, gather_iso_observers)
        for file in part_files:
            logger.info(f"Adding the following file to the ISO: {file}")
            copy_with_progress(src_path=file,
                               dst_path=concatenated_iso_path,
                               progress_callback=parts_progress_reporter.report_progress,
                               chunk_size_kb=20000)
        parts_progress_reporter.notify_observers_process_completed()
        logger.info("Finished concatenation.")
    else:
        logger.info("No part files found.")

    unmount_directory(root_path)


class MultipleFilesError(Exception):
    pass


def verify_iso_file(root_mount_path_directory:str):
    iso_files = glob.glob(os.path.join(root_mount_path_directory, "*.iso"))

    if not iso_files:
        raise FileNotFoundError("We expected at least one ISO file. Make sure to copy an ISO file onto your USB.")
    elif len(iso_files) > 1:
        msg = ["Too many ISO files given."]
        msg.append(f"Files in {root_mount_path_directory} directory:")
        msg += iso_files
        raise MultipleFilesError('\n'.join(msg))
    else:
        logger.info(f"ISO file in {root_mount_path_directory} directory: {iso_files[0]}")
        return iso_files[0]


def handle_output(process, handler_info, handler_error):
    for line in iter(process.readline, b''):
        # remove ANSI escape sequences
        message = re.sub(r'\x1b\[.*?[@-~]', '', line.decode()).strip()
        handler_error(message) if "Error:" in message else handler_info(message)


def run_woeusb(iso_file, top_level_device):
    cmd = ['woeusb', '--target-filesystem', 'NTFS', '--device', '--no-color', iso_file, top_level_device]
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
        with ThreadPoolExecutor(max_workers=2) as executor:
            executor.submit(handle_output, process.stdout, logger.info, logger.error)
            executor.submit(handle_output, process.stderr, logger.info, logger.error)

        process.wait()
        if process.returncode != 0:
            raise Exception(f'woeusb command exited with return code {process.returncode}')


class LoggerWriter:
    def __init__(self, level):
        self.level = level

    def write(self, message):
        if message.rstrip() != "":
            logger.log(self.level, message.rstrip())

    def flush(self):
        pass


def run_woeusbv2(iso_file, top_level_device):
    logger.addHandler(logging.StreamHandler())  # Or any other Handler
    sys.stdout = LoggerWriter(logger.level)
    args_list = [iso_file,
                 top_level_device,
                 '--device',
                 '--no-color',
                 '--label', 'Windows USB',
                 '--target-filesystem', 'NTFS',
                 '--workaround-skip-grub']
    result = init(args_list=args_list)
    if isinstance(result, list) is False:
        return

    source_fs_mountpoint, target_fs_mountpoint, temp_directory, \
        install_mode, source_media, target_media, \
        workaround_bios_boot_flag, skip_legacy_bootloader, target_filesystem_type, \
        new_file_system_label, verbose, debug, parser = result

    return_code = -1
    try:
        print(f'source_fs_mountpoint: {source_fs_mountpoint}')
        print(f'target_fs_mountpoint: {target_fs_mountpoint}')
        print(f'temp_directory: {temp_directory}')
        print(f'install_mode: {install_mode}')
        print(f'source_media: {source_media}')
        print(f'target_media: {target_media}')
        print(f'workaround_bios_boot_flag: {workaround_bios_boot_flag}')
        print(f'skip_legacy_bootloader: {skip_legacy_bootloader}')
        print(f'target_filesystem_type: {target_filesystem_type}')
        print(f'new_file_system_label: {new_file_system_label}')
        print(f'verbose: {verbose}')
        print(f'debug: {debug}')
        print(f'parser: {parser}')
        return_code = WoeUSB.core.main(source_fs_mountpoint, target_fs_mountpoint, source_media, target_media,
                                       install_mode, temp_directory, target_filesystem_type, workaround_bios_boot_flag,
                                       parser, skip_legacy_bootloader)
    except KeyboardInterrupt:
        pass
    except Exception as error:
        logger.error(error)

    WoeUSB.core.cleanup(source_fs_mountpoint, target_fs_mountpoint, temp_directory, target_media)
    if return_code != 0:
        raise Exception('An Error has occurred running WoeUSB')



class PostProcessTask(Enum):
    SHUTDOWN = auto()
    RESTART = auto()
    NONE = auto()


def execute_post_process_task(task: PostProcessTask):
    """Execute post process task based on provided task"""
    if task == PostProcessTask.SHUTDOWN:
        shutdown_system()
    elif task == PostProcessTask.RESTART:
        restart_system()
    else:
        logger.info("The process is completed.")


def shutdown_system():
    """Shutdown the system"""
    try:
        subprocess.call(["shutdown", "-h", "now"])
    except Exception as e:
        logger.error(f"Error occured while trying to shutdown system: {str(e)}")


def restart_system():
    """Restart the system"""
    try:
        subprocess.call(["reboot"])
    except Exception as e:
        logger.error(f"Error occured while trying to restart system: {str(e)}")


def is_os_running_in_virtualbox() -> bool:
    try:
        result = subprocess.run(['systemd-detect-virt'], stdout=subprocess.PIPE, check=True)
        output = result.stdout.decode('utf-8').strip()
        return output.lower() == 'oracle'
    except Exception as e:
        logger.info(f"An error occurred while trying to detect if the OS is running in VirtualBox: {str(e)}")
        return False


class StatusMessage:
    def __init__(self, status, description):
        self.status = status
        self.description = description


class CmosObserver:
    def update(self, message: StatusMessage):
        log_message = f"Status: {message.status}, Description: {message.description}"
        logger.info(log_message)


class CmosSubject:
    def __init__(self):
        self._observers = []

    def attach(self, observer):
        self._observers.append(observer)

    def notify(self, message):
        for observer in self._observers:
            observer.update(message)


def main(cmos_observers=None, gather_iso_observers=None, post_process_task=PostProcessTask.NONE):
    if cmos_observers is None:
        cmos_observers = []
    cmos_subject = CmosSubject()
    # Add the default observer
    cmos_subject.attach(CmosObserver())
    # Add any additional observers
    for observer in cmos_observers:
        cmos_subject.attach(observer)

    if gather_iso_observers is None:
        gather_iso_observers = []

    try:
        cmos_subject.notify(StatusMessage("Starting CMOS", "CMOS is starting."))
        if platform.system() == 'Windows':
            logger.info("You are currently running Windows. CMOS only supports X86-64 Linux based operating systems.")
            return
        user_home_directory_path = os.path.expanduser("~")
        device_mount_directory_path = os.path.join(user_home_directory_path, "mnt")
        iso_root_mount_path_directory = os.path.join(user_home_directory_path, "iso")

        cmos_subject.notify(StatusMessage("Step 1/5: Searching for CMOS USB", "This should take less than a minute."))
        cmos_usb = check_block_devices(device_mount_directory_path)

        cmos_subject.notify(StatusMessage("Step 2/5: Gather ISO File(s)",
                                          """Progress should be consistent and not stall out."""))
        gather_and_extract_iso_files(cmos_usb.mountpoint, iso_root_mount_path_directory, gather_iso_observers)

        cmos_subject.notify(StatusMessage("Step 3/5: Verify ISO File(s)", "This should take less than a minute."))
        iso_file = verify_iso_file(iso_root_mount_path_directory)

        cmos_subject.notify(StatusMessage("Step 4/5: Get Top level device", "This should take less than a second."))
        top_level_device = get_top_level_device(cmos_usb.name)

        cmos_subject.notify(StatusMessage("Step 5/5: Run WoeUSB", "N/A"))
        run_woeusbv2(iso_file, top_level_device)

        cmos_subject.notify(
            StatusMessage("CMOS has completed successfully!",
                          "It is now safe to shutdown your PC. CMOS will do this automatically for you in 30 seconds."))
        time.sleep(30)
        execute_post_process_task(post_process_task)
        exit(0)
    except Exception as e:
        logger.error(e)
        logger.error("CMOS experienced a failure!")
        cmos_subject.notify(StatusMessage("CMOS experienced a failure!", "Error occurred."))
        logger.info("Sleeping for 30 seconds before terminating.")
        time.sleep(30)
        exit(0)


