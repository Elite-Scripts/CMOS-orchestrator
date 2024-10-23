import uuid

import pytest
import subprocess

from CMOS_orchestrator import core
from CMOS_orchestrator.core import BlockDevice
from unittest.mock import patch


@patch('subprocess.check_output')
@pytest.mark.parametrize(
    "device, mock_output, expected_result",
    [
        ('/dev/sda', 'sda', '/dev/sda'),
        ('/dev/sda1', 'sda', '/dev/sda'),
        ('/dev/sda2', 'sda', '/dev/sda'),
        ('/dev/sda3', 'sda', '/dev/sda'),
        ('/dev/sdb', '', '/dev/sdb'),
        ('/dev/sdc', 'sdc', '/dev/sdc'),
        ('/dev/sdc1', 'sdc', '/dev/sdc'),
        ('/dev/sr0', '', '/dev/sr0'),
        ('/dev/mmcblk0', '', '/dev/mmcblk0'),
        ('/dev/mmcblk0boot0', '', '/dev/mmcblk0boot0'),
        ('/dev/mmcblk0boot1', '', '/dev/mmcblk0boot1'),
    ]
)
def test_get_top_level_device(mock_subprocess, device, mock_output, expected_result):
    mock_subprocess.return_value = mock_output
    result = core.get_top_level_device(device)
    assert result == expected_result


def test_get_possible_mounts():
    real_data = """
    {
        "blockdevices": [
            {"name": "/dev/sda", "rm": false, "mountpoint": null},
            {"name": "/dev/sda1", "rm": false, "mountpoint": "/boot/efi"},
            {"name": "/dev/sda2", "rm": false, "mountpoint": "/"},
            {"name": "/dev/sda3", "rm": false, "mountpoint": "[SWAP]"},
            {"name": "/dev/sdb", "rm": false, "mountpoint": null},
            {"name": "/dev/sdc", "rm": true, "mountpoint": null},
            {"name": "/dev/sdc1", "rm": true, "mountpoint": "/media/warfront1/D-LIVE 12_7"},
            {"name": "/dev/sr0", "rm": true, "mountpoint": null},
            {"name": "/dev/mmcblk0", "rm": false, "mountpoint": null},
            {"name": "/dev/mmcblk0boot0", "rm": false, "mountpoint": null},
            {"name": "/dev/mmcblk0boot1", "rm": false, "mountpoint": null}
        ]
    }
    """
    expected_response = [
        BlockDevice(name='/dev/sda', rm=False, mountpoint=None),
        BlockDevice(name='/dev/sda1', rm=False, mountpoint='/boot/efi'),
        BlockDevice(name='/dev/sda2', rm=False, mountpoint='/'),
        BlockDevice(name='/dev/sda3', rm=False, mountpoint='[SWAP]'),
        BlockDevice(name='/dev/sdb', rm=False, mountpoint=None),
        BlockDevice(name='/dev/sdc', rm=True, mountpoint=None),
        BlockDevice(name='/dev/sdc1', rm=True, mountpoint='/media/warfront1/D-LIVE 12_7'),
        BlockDevice(name='/dev/sr0', rm=True, mountpoint=None),
        BlockDevice(name='/dev/mmcblk0', rm=False, mountpoint=None),
        BlockDevice(name='/dev/mmcblk0boot0', rm=False, mountpoint=None),
        BlockDevice(name='/dev/mmcblk0boot1', rm=False, mountpoint=None)
    ]

    # Mock subprocess.run
    with patch('subprocess.run') as mocked_run:
        # When subprocess.run is called, it would return this
        run_output = subprocess.CompletedProcess(args=None, returncode=0, stdout=real_data, stderr='')
        mocked_run.return_value = run_output

        # Call your function
        response = core.get_block_devices()

        # Verify your function
        assert response == expected_response

        # Ensure subprocess.run was called with the right arguments
        expected_args = (['lsblk', '-lpJ', '-o', 'NAME,RM,MOUNTPOINT'],)
        expected_kwargs = {'capture_output': True, 'text': True, 'check': True}
        mocked_run.assert_called_once_with(*expected_args, **expected_kwargs)


def test_create_directory_and_mount():
    test_mount = "/test_mount"
    expected_uuid4 = "c7d392ff-503f-4bd5-8b5d-9b90606f4154"
    expected_path_to_mount = "/mount_/test_mount_c7d392ff-503f-4bd5-8b5d-9b90606f4154"

    with patch('os.makedirs', autospec=True) as mock_makedirs, \
            patch('os.system', autospec=True) as mock_system, \
            patch('uuid.uuid4', return_value=uuid.UUID(expected_uuid4)):
        # uuid is mocked here to return a predefined UUID and os functions are replaced with mock

        # Call the function
        result = core.create_directory_and_mount(test_mount)

    # Assertions
    assert result == expected_path_to_mount  # It should return correct mount path
    mock_makedirs.assert_called_once_with(expected_path_to_mount,
                                          exist_ok=True)  # It should try to create the directory
    mock_system.assert_called_once_with(
        "sudo mount {0} {1}".format(test_mount, expected_path_to_mount))  # It should attempt to mount the device
