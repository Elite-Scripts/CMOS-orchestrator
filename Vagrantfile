require 'pathname'
require 'securerandom'

current_dir = Dir.pwd
uuid = SecureRandom.uuid
secondary_storage_device_path = Pathname.new(current_dir + "/.vagrant/machines/default/virtualbox/secondary_#{uuid}.vmdk")
secondary_storage_device_path_str = secondary_storage_device_path.to_s


Vagrant.configure("2") do |config|
  config.vm.box = "debian/bookworm64"
  config.vm.provider "virtualbox" do |v|
        v.memory = 4096
        v.cpus = 4

        # Attach the secondary disk
        if secondary_storage_device_path.exist?
            puts "Skipping the creation of the secondary storage device as it has already been created."
        else
            v.customize ['createhd', '--filename', secondary_storage_device_path_str, '--size', 10 * 1024, '--variant', 'Fixed']
        end
        v.customize ['storageattach', :id, '--storagectl', 'SATA Controller', '--port', 1, '--device', 0, '--type', 'hdd', '--medium', secondary_storage_device_path_str]
    end

  config.vm.provision "shell", privileged: false, inline: <<-SHELL
    sudo apt-get update -y                  # Fetches the list of available updates
    sudo apt-get upgrade -y              # Strictly upgrades the current packages
    #sudo apt-get dist-upgrade -y           # Installs updates (new ones)
    sudo apt-get install -y psmisc curl git zstd rsync
    sudo apt install -y util-linux dosfstools ntfs-3g p7zip-full parted grub-pc
    file="cpython-3.12.7+20241016-x86_64-unknown-linux-gnu-debug-full.tar.zst"
    url="https://github.com/indygreg/python-build-standalone/releases/download/20241016/cpython-3.12.7+20241016-x86_64-unknown-linux-gnu-debug-full.tar.zst"
    if [ ! -f "$file" ]; then
        curl -LO $url
    else
        echo "File $file already exists."
    fi
    tar -I zstd -xf "./cpython-3.12.7+20241016-x86_64-unknown-linux-gnu-debug-full.tar.zst"
    sudo rsync -a $HOME/python/ /usr/bin/python3.12/
    echo 'export PATH="/usr/bin/python3.12/install/bin/:$PATH"' >> ~/.bashrc
    export PATH="/usr/bin/python3.12/install/bin/:$PATH"
    python3.12 --version
    sudo /usr/bin/python3.12/install/bin/pip3.12 install --force-reinstall /vagrant

    echo "Starting to attempt to unmount /mnt/temp"
    MOUNT_POINT="/mnt/temp"

    # Check if /mnt/temp is a mountpoint
    if mountpoint -q "$MOUNT_POINT"; then
        PIDS=$(sudo fuser -m $MOUNT_POINT 2>/dev/null)
        if [ -n "$PIDS" ]; then
           sudo kill -9 $PIDS
        fi
        sudo umount -f $MOUNT_POINT
        echo "Done attempting to unmount /mnt/temp"
    else
        echo "$MOUNT_POINT is not a mount point"
    fi
    sleep 1
    DISK_NAME=$(lsblk -d -o NAME,SIZE -l | grep '10G' | awk '{print $1}')
    sudo mkfs.vfat -I -F 32 /dev/${DISK_NAME}
    sudo mkdir /mnt/temp
    sudo mount /dev/${DISK_NAME}1 /mnt/temp
    sudo rsync -vPW --exclude='*.md' /vagrant/src/integration_test/python/CMOS_orchestrator/resources/test_isos/* /mnt/temp
    sudo mkdir /mnt/temp/boot /mnt/temp/EFI /mnt/temp/live /mnt/temp/syslinux
    sudo touch /mnt/temp/CMOS
    sudo umount /mnt/temp
    sudo rm -rf /root/iso/*

    echo 'Defaults secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/bin/python3.12/install/bin/"' | sudo tee /etc/sudoers.d/my_sudo
    sudo chmod 0440 /etc/sudoers.d/my_sudo
    sudo chown root:root /etc/sudoers.d/my_sudo
  SHELL
end