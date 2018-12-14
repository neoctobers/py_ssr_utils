# coding:utf-8
import os
import dotenv
import tempfile
import time
import subprocess
import requests
import xprint as xp


class Tester():
    def __init__(self):
        dotenv.load_dotenv()

        self._python = os.getenv('PYTHON', '/usr/bin/python3')
        self._python_ssr = os.getenv('PYTHON_SSR', '/data/shadowsocksr/shadowsocks/local.py')

        self._server = None
        self._port = None
        self._method = None
        self._password = None
        self._protocol = None
        self._proto_param = None
        self._obfs = None
        self._obfs_param = None

        self._local_port = None
        self._requests_proxies = None

        self._ip = None
        self._country = None
        self._country_code = None

    def set_config(self,
                   server='',
                   port='',
                   method='',
                   password='',
                   protocol='origin',
                   proto_param='',
                   obfs='plain',
                   obfs_param='',
                   local_port=13431,
                   ):
        self._server = server
        self._port = port
        self._method = method
        self._password = password
        self._protocol = protocol
        self._proto_param = proto_param
        self._obfs = obfs
        self._obfs_param = obfs_param

        self._local_port = local_port

        self._path_to_config = os.path.join(tempfile.gettempdir(), 'ssr_tester_{time}.json'.format(
            time=str(time.time()).replace('.', '').ljust(17, '0'),
        ))

        self._requests_proxies = {
            'http': 'socks5://127.0.0.1:{local_port}'.format(local_port=self._local_port),
            'https': 'socks5://127.0.0.1:{local_port}'.format(local_port=self._local_port),
        }

        # write config
        xp.about_t('Generating ', self._path_to_config)
        with open(self._path_to_config, 'wb') as f:
            json_content = '{\n'
            json_content += '    "server": "{server}",\n' \
                            '    "server_port": {server_port},\n' \
                            '    "method": "{method}",\n' \
                            '    "password": "{password}",\n' \
                            '    "protocol": "{protocol}",\n' \
                            '    "protocol_param": "{protocol_param}",\n' \
                            '    "obfs": "{obfs}",\n' \
                            '    "obfs_param": "{obfs_param}",\n\n' \
                            '    "local_address": "127.0.0.1",\n' \
                            '    "local_port": {local_port}' \
                            ''.format(server=self._server,
                                      server_port=self._port,
                                      method=self._method,
                                      password=self._password,
                                      protocol=self._protocol,
                                      protocol_param=self._proto_param,
                                      obfs=self._obfs,
                                      obfs_param=self._obfs_param,
                                      local_port=self._local_port,
                                      )
            json_content += '\n}'

            f.write(json_content.encode('utf-8'))
            xp.success('Done.')

    def check(self):
        cmd = '{python} {python_ssr} -c {ssr_config}'.format(
            python=self._python,
            python_ssr=self._python_ssr,
            ssr_config=self._path_to_config,
        )

        # sub progress
        xp.about_t('Start a sub progress of SSR')
        sub_progress_of_ssr = subprocess.Popen(
            cmd.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
        )
        xp.wr(xp.Fore.LIGHTCYAN_EX + 'PID {pid} '.format(pid=sub_progress_of_ssr.pid))

        # wait, during the progress launching.
        for i in range(0, 5):
            xp.wr(xp.Fore.LIGHTBLUE_EX + '.')
            xp.fi()
            time.sleep(1)
        xp.success(' Next.')

        # Request for IP
        xp.about_t('Try to request for the IP address')
        my_ip = None
        try:
            my_ip = requests.get(
                url='https://api.myip.com/',
                proxies=self._requests_proxies,
                timeout=15,
            ).json()
        except ConnectionError:
            xp.fx()
            xp.error('A proxy error occurred.')
            xp.error('A proxy error occurred.')
            xp.error('A proxy error occurred.')
        except Exception as e:
            xp.fx()
            xp.error(e)
        finally:
            os.killpg(os.getpgid(sub_progress_of_ssr.pid), 9)
            os.remove(self._path_to_config)

        if my_ip:
            self._ip = my_ip['ip']
            self._country = my_ip['country']
            self._country_code = my_ip['cc']

            xp.success(self._ip)
            xp.fx()

            return True

        return False
