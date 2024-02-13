import os
import platform
import subprocess
import shutil
import re
import sys
import socket
import requests
import getpass
from pathlib import Path


# Function to get OS information
def get_os_info():
    os_info = {"system": platform.system(), "release": platform.release(), "version": platform.version(),
               "machine": platform.machine(), "platform": platform.platform(), "uname": platform.uname(),
               }

    return os_info


# Function to get the OS version
def get_os_version():
    version_info = platform.version().split('.')
    return int(version_info[0]) if version_info else None


# Function to get the sudo command
def get_sudo_cmd():
    if os.geteuid() != 0:
        if len(sys.argv) > 1:
            return ['sudo', '-E', '-H']
        else:
            return ['sudo', '-E']
    return []


# Function to install dependencies on Debian/Ubuntu
def install_dependencies_debian():
    required_packages = [
        "sudo", "software-properties-common", "dnsutils", "curl", "git", "locales", "rsync",
        "apparmor", "python3", "python3-setuptools", "python3-apt", "python3-venv", "python3-pip",
        "aptitude", "direnv", "iptables"
    ]
    required_packages_arm64 = ["gcc", "python3-dev", "libffi-dev", "libssl-dev", "make"]

    # Disable interactive apt functionality
    os.environ["DEBIAN_FRONTEND"] = "noninteractive"

    # Update apt database, update all packages and install Ansible + dependencies
    subprocess.run(["sudo", "apt", "update", "-y"], check=True)
    subprocess.run(["yes", "|", "sudo", "apt-get", "-o", "Dpkg::Options::='--force-confold'", "-fuy", "dist-upgrade"],
                   check=True)
    subprocess.run(["yes", "|", "sudo", "apt-get", "-o", "Dpkg::Options::='--force-confold'", "-fuy",
                    "install"] + required_packages, check=True)
    subprocess.run(["yes", "|", "sudo", "apt-get", "-o", "Dpkg::Options::='--force-confold'", "-fuy", "autoremove"],
                   check=True)
    if os.uname().machine == "aarch64":
        subprocess.run(["yes", "|", "sudo", "apt", "install", "-fuy"] + required_packages_arm64, check=True)

    os.environ["DEBIAN_FRONTEND"] = ""  # Reset DEBIAN_FRONTEND


# Function to install dependencies on CentOS/Rocky Linux/AlmaLinux/Fedora
def install_dependencies_centos():
    required_packages = [
        "sudo", "bind-utils", "curl", "git", "rsync",
        "https://kojipkgs.fedoraproject.org//vol/fedora_koji_archive02/packages/"
        "direnv/2.12.2/1.fc28/x86_64/direnv-2.12.2-1.fc28.x86_64.rpm"
    ]

    if get_os_version() == 9:
        required_packages += [
            "python3", "python3-setuptools", "python3-pip", "python3-firewall"
        ]
    else:
        required_packages += [
            "python39", "python39-setuptools", "python39-pip", "python3-firewall",
            "kmod-wireguard",
            "https://ftp.gwdg.de/pub/linux/elrepo/elrepo/el8/x86_64/RPMS/"
            "kmod-wireguard-1.0.20220627-4.el8_7.elrepo.x86_64.rpm"
        ]

    subprocess.run(["sudo", "dnf", "update", "-y"], check=True)
    subprocess.run(["sudo", "dnf", "install", "-y", "epel-release"], check=True)
    subprocess.run(["sudo", "dnf", "install", "-y"] + required_packages, check=True)


# Function to clone the Ansible playbook
def clone_ansible_playbook():
    playbook_dir = os.path.join(Path.home(), "ansible-vpn")
    if os.path.isdir(playbook_dir):
        os.chdir(playbook_dir)
        subprocess.run(["git", "pull"], check=True)
    else:
        subprocess.run(["git", "clone", "https://github.com/notthebee/ansible-vpn", playbook_dir], check=True)


# Function to set up a Python venv
def setup_python_venv():
    python_executable = shutil.which("python3.9") or shutil.which("python3")
    venv_path = os.path.join(Path.home(), "ansible-vpn", ".venv")
    if not os.path.isdir(venv_path):
        subprocess.run([python_executable, "-m", "venv", venv_path], check=True)
    os.environ["VIRTUAL_ENV"] = venv_path
    os.environ["PATH"] = os.path.join(venv_path, "bin") + os.pathsep + os.environ["PATH"]
    subprocess.run(["python", "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run(["python", "-m", "pip", "install", "-r", "requirements.txt"],
                   cwd=os.path.join(Path.home(), "ansible-vpn"), check=True)


# Function to install Galaxy requirements
def install_galaxy_requirements():
    subprocess.run(["ansible-galaxy", "install", "--force", "-r", "requirements.yml"],
                   cwd=os.path.join(Path.home(), "ansible-vpn"), check=True)


# Function to check if running on an AWS EC2 instance
def is_aws_ec2_instance():
    try:
        requests.get("http://169.254.169.254/latest/meta-data/ami-id", timeout=5)
        return True
    except (requests.RequestException, socket.timeout):
        return False


# Function to prompt user for input
def prompt_user(prompt, default=None):
    user_input = input(prompt + f" [{default}]: ") if default else input(prompt + ": ")
    return user_input.strip() or default


# Function to check if a string is a valid DNS name
def is_valid_dns_name(dns_name):
    return re.match(r"^[a-z0-9.\-]+$", dns_name)


# Function to get public IP address
def get_public_ip():
    try:
        response = requests.get("https://api.ipify.org")
        return response.text.strip()
    except requests.RequestException:
        return None


# Function to validate DNS resolution
def validate_dns_resolution(domain):
    try:
        domain_ip = socket.gethostbyname(domain)
        return domain_ip
    except socket.gaierror:
        return None


# Function to run certbot in dry-run mode
def run_certbot_dry_run(root_host, adguard_enable):
    staging_flag = "--staging" if adguard_enable else ""
    subprocess.run(
        ["sudo", ".venv/bin/certbot", "certonly", "--non-interactive", "--break-my-certs", "--force-renewal",
         "--agree-tos", "--email", "root@localhost.com", "--standalone", staging_flag,
         "-d", root_host, "-d", f"wg.{root_host}", "-d", f"auth.{root_host}"],
        cwd=os.path.join(Path.home(), "ansible-vpn"), check=True)


# Function to create custom.yml file with user input
def create_custom_yml():
    custom_yml_path = os.path.join(Path.home(), "ansible-vpn", "custom.yml")
    if os.path.exists(custom_yml_path):
        print("custom.yml already exists. Running the playbook...")
        print("If you want to change something (e.g. username, domain name, etc.)")
        print("Please edit custom.yml or secret.yml manually, and then re-run this script")
        subprocess.run(["ansible-playbook", "--ask-vault-pass", "run.yml"],
                       cwd=os.path.join(Path.home(), "ansible-vpn"), check=True)
        sys.exit(0)

    print("Welcome to ansible-vpn!")
    print("This script is interactive")
    print("If you prefer to fill in the custom.yml file manually,")
    print("press [Ctrl+C] to quit this script")

    username = prompt_user("Enter your desired UNIX username")
    while not re.match(r"^[a-z0-9]*$", username):
        print("Invalid username")
        print("Make sure the username only contains lowercase letters and numbers")
        username = prompt_user("Username")

    user_password = getpass.getpass("Enter your user password: ")
    while len(user_password) >= 60:
        print("The password is too long")
        print("OpenSSH does not support passwords longer than 72 characters")
        user_password = getpass.getpass("Enter your user password: ")

    user_password2 = getpass.getpass("Repeat password: ")
    while user_password != user_password2:
        print("The passwords don't match")
        user_password = getpass.getpass("Enter your user password: ")
        user_password2 = getpass.getpass("Repeat password: ")

    adguard_enable = input(
        "Would you like to enable Adguard, Unbound and DNS-over-HTTP for secure DNS resolution "
        "with ad blocking functionality? [y/N]: ").strip().lower() == "y"

    domain_name = prompt_user("Enter your domain name")
    while not is_valid_dns_name(domain_name):
        print("Invalid domain name")
        domain_name = prompt_user("Domain name")

    # TODO: Other inputs and validations...

    # Write inputs to custom.yml file
    with open(custom_yml_path, "w") as f:
        f.write(f"username: \"{username}\"\n")
        # Write other inputs...


# Function to encrypt variables and run the playbook
def encrypt_variables_and_run_playbook():
    # Encrypt variables
    subprocess.run(["ansible-vault", "encrypt", os.path.join(Path.home(), "ansible-vpn", "secret.yml")], check=True)

    # Run the playbook
    launch_playbook = input("Would you like to run the playbook now? [y/N]: ").strip().lower()
    if launch_playbook == "y":
        playbook_dir = os.path.join(Path.home(), "ansible-vpn")
        if os.geteuid() != 0:
            print("Please enter your current sudo password now")
            subprocess.run(["ansible-playbook", "--ask-vault-pass", "-K", "run.yml"], cwd=playbook_dir)
        else:
            subprocess.run(["ansible-playbook", "--ask-vault-pass", "run.yml"], cwd=playbook_dir)
    else:
        print("You can run the playbook by executing the bootstrap script again:")
        print("cd ~/ansible-vpn && bash bootstrap.sh")
        sys.exit()


# Main function
def main():
    # Install dependencies based on OS
    if get_os_info()["platform"].lower() in ("debian", "ubuntu"):
        install_dependencies_debian()
    elif get_os_info()["platform"].lower() in ("centos", "rocky", "almalinux", "fedora"):
        install_dependencies_centos()

    # Clone the Ansible playbook
    clone_ansible_playbook()

    # Set up Python venv
    setup_python_venv()

    # Install Galaxy requirements
    install_galaxy_requirements()

    # Check if running on an AWS EC2 instance
    aws_ec2 = is_aws_ec2_instance()

    # Run certbot in dry-run mode
    root_host = "example.com"  # Replace with actual domain name
    adguard_enable = False  # Set to True if Adguard is enabled
    run_certbot_dry_run(root_host, adguard_enable)

    # Create custom.yml file with user input
    create_custom_yml()

    # Encrypt variables and run the playbook
    encrypt_variables_and_run_playbook()


if __name__ == "__main__":
    main()
