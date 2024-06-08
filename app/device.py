from dataclasses import dataclass
from django.conf import settings
import paramiko, json


@dataclass
class DeviceHandler():
    exporter_host = '192.168.1.232'
    exporter_username = 'spectyte5'
    exporter_password = settings.EXPORTER_PASSWORD 
    targets_username = 'root'
    targets_password = settings.TARGETS_PASSWORD 
    ssh = paramiko.SSHClient()
    config_path = 'config.json'
    devices_dict = {}

    def __post_init__(self):
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        with open(self.config_path) as f:
            config = json.load(f)
            
        for device_config in config['devices']:
            name = device_config.pop('name')
            self.devices_dict[name] = {**device_config}

    def check_serial_connection(self, device):
        if self.devices_dict[device]['usb']:
            self.ssh.connect(self.exporter_host, username=self.exporter_username, password=self.exporter_password)
            _, stdout, _ = self.ssh.exec_command(f"ps auxw | grep -E 'SCREEN' | grep -v grep | grep {self.devices_dict[device]['usb']}")
            busy = stdout.read().decode().strip() if stdout else None
            _, stdout, _ = self.ssh.exec_command(f"ls {self.devices_dict[device]['usb']}")
            serial = stdout.read().decode().strip() if stdout else None
            busy_output = busy.split()[1] if busy else 'Free'
            serial_output = 'OK' if serial else 'Error'
            return busy_output, serial_output
        return '-', '-'

    def check_enviromental_variables(self, device, ip):
        self.ssh.connect(ip, username=self.targets_username, password=self.targets_password)
        envs = []
        for var in self.devices_dict[device]['variables']:
            _, stdout, _ = self.ssh.exec_command(f"printenv {var}")
            if stdout:
                full = f'{stdout.read().decode().strip()}'
                cleaned = f'{var} : {full}'
                envs.append(cleaned)
        return envs if envs else '-'

    def check_systemctl_status(self, device, ip):
        self.ssh.connect(ip, username=self.targets_username, password=self.targets_password)
        services = []
        for service in self.devices_dict[device]['systemctl']:
            _, stdout, _ = self.ssh.exec_command(f"systemctl --no-pager status {service} | grep Active:")
            if stdout:
                full = f'{stdout.read().decode().strip()}'
                split = full.split()[1:6]
                cleaned = f'{service} : ' + ' '.join(split)
                services.append(cleaned)
        return services if services else '-'

    def check_docker_containers(self, ip):
        self.ssh.connect(ip, username=self.targets_username, password=self.targets_password)
        _, stdout, _ = self.ssh.exec_command("docker ps --format {{.Names}}")
        containers = stdout.read().decode().strip() if stdout else None
        return containers if containers else '-'

    def check_ssh_connection(self, device):
        self.ssh.connect(self.exporter_host, username=self.exporter_username, password=self.exporter_password)
        _, stdout, _ = self.ssh.exec_command(f"cat /etc/hosts | grep {self.devices_dict[device]['hostname']}")
        ip = stdout.read().decode().split()[0] if stdout else 'None'
        envs = self.check_enviromental_variables(device, ip)
        services = self.check_systemctl_status(device, ip)
        containers = self.check_docker_containers(ip)
        return ip, envs, services, containers

    def set_status(self, device):
        if not self.devices_dict[device]['ip']:
            status = 'SSH_ERRORS'
        elif self.devices_dict[device]['usb'] and self.devices_dict[device]['serial'] != 'OK':
            status = 'SERIAL_ERRORS'
        elif self.devices_dict[device]['usb'] and self.devices_dict[device]['busy'] != 'Free':
            status = 'BUSY'
        else:
            status = 'OK'
        return status

    def get_devices(self):
        for device in self.devices_dict.keys():
            self.devices_dict[device]['busy'], self.devices_dict[device]['serial'] = self.check_serial_connection(device)
            self.devices_dict[device]['ip'], self.devices_dict[device]['variables'], self.devices_dict[device]['systemctl'], \
                self.devices_dict[device]['docker'] = self.check_ssh_connection(device)
            self.devices_dict[device]['status'] = self.set_status(device)
        return self.devices_dict