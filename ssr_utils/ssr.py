# coding:utf-8
import os
import sys
import time
import socket
import requests
import requests_cache
import list_ext
import subprocess
import dotenv
import tempfile
import common_patterns
import xprint as xp
import xbase64
import urllib.parse
from .errors import SystemNotSupportedException

# Load .env
dotenv.load_dotenv()


class SSR:
    def __init__(self):
        self._server = None
        self._port = None
        self._method = None
        self._password = None
        self._protocol = None
        self._proto_param = None
        self._obfs = None
        self._obfs_param = None

        self._remarks = None
        self._group = None

        self._server_ip = None
        self._server_domain = None

        self._local_address = None
        self._local_port = None
        self._path_to_config = None

        self._exit_ip = None
        self._exit_country = None
        self._exit_country_code = None

        self._cmd = None
        self._sub_progress = None
        pass

    def __reset_attributes(self):
        self._server = ''
        self._port = 443
        self._method = ''
        self._password = ''
        self._protocol = 'origin'
        self._proto_param = None
        self._obfs = 'plain'
        self._obfs_param = None

        self._remarks = None
        self._group = None

        self._server_ip = None
        self._server_domain = None

        self._local_address = None
        self._local_port = None
        self._path_to_config = None

        self._exit_ip = None
        self._exit_country = None
        self._exit_country_code = None

    @property
    def server(self):
        return self._server

    @property
    def port(self):
        return self._port

    @property
    def method(self):
        return self._method

    @property
    def password(self):
        return self._password

    @property
    def protocol(self):
        return self._protocol

    @property
    def proto_param(self):
        return self._proto_param or ''

    @property
    def obfs(self):
        return self._obfs

    @property
    def obfs_param(self):
        return self._obfs_param or ''

    @property
    def remarks(self):
        return self._remarks or ''

    @remarks.setter
    def remarks(self, value: str):
        self._remarks = value

    @property
    def group(self):
        return self._group or ''

    @group.setter
    def group(self, value: str):
        self._group = value

    @property
    def server_ip(self):
        if self._server_ip:
            return self._server_ip

        # ip == server?
        if common_patterns.is_ip_address(self.server):
            self._server_ip = self.server
            return self._server_ip

        # domain
        self._server_domain = self.server

        # domain 2 exit_ip
        self._server_ip = socket.gethostbyname(self._server_domain)
        return self._server_ip

    @property
    def server_domain(self):
        if self._server_domain:
            return self._server_domain

        # domain
        if not common_patterns.is_ip_address(self.server):
            self._server_domain = self.server
            return self._server_domain

        # None
        return self._server_domain

    @property
    def local_address(self):
        return self._local_address or '127.0.0.1'

    @local_address.setter
    def local_address(self, value: str):
        self._local_address = value

    @property
    def local_port(self):
        return self._local_port or 13431

    @local_port.setter
    def local_port(self, value: int):
        self._local_port = value

    @property
    def path_to_config(self):
        return self._path_to_config or 'shadowsocksr.json'

    @path_to_config.setter
    def path_to_config(self, value: str):
        self._path_to_config = value

    @property
    def exit_ip(self):
        return self._exit_ip

    @property
    def exit_country(self):
        return self._exit_country

    @property
    def exit_country_code(self):
        return self._exit_country_code

    @property
    def invalid_attributes(self):
        keys = [
            'server',
            'port',
            'method',
            'password',
            'protocol',
            'obfs',
        ]

        for key in keys:
            if not getattr(self, '_{}'.format(key)):
                xp.error('Attribute `{}` is invalid.'.format(key))
                return True
        return False

    def load(self, obj):
        self.__reset_attributes()

        keys = {
            'server': '',
            'port': 443,
            'method': '',
            'password': '',
            'protocol': 'origin',
            'proto_param': '',
            'obfs': 'plain',
            'obfs_param': '',

            'remarks': None,
            'group': None,
        }

        for key, value in keys.items():
            setattr(self, '_{}'.format(key), getattr(obj, key, value))

    def set(self,
            server: str = '',
            port: int = 443,
            method: str = '',
            password: str = '',
            protocol: str = 'origin',
            proto_param: str = '',
            obfs: str = 'plain',
            obfs_param: str = '',

            remarks: str = None,
            group: str = None,
            ):
        self.__reset_attributes()

        self._server = server
        self._port = port
        self._method = method
        self._password = password
        self._protocol = protocol
        self._proto_param = proto_param
        self._obfs = obfs
        self._obfs_param = obfs_param

        if remarks:
            self._remarks = remarks
        if group:
            self._group = group

    @property
    def config(self):
        # check attributes
        if self.invalid_attributes:
            return None

        return {
            'server': self._server,
            'port': self._port,
            'method': self._method,
            'password': self._password,
            'protocol': self._protocol,
            'proto_param': self._proto_param,
            'obfs': self._obfs,
            'obfs_param': self._obfs_param,

            'remarks': self.remarks,
            'group': self.group,
        }

    @property
    def url(self):
        # check attributes
        if self.invalid_attributes:
            return None

        prefix = '{server}:{port}:{protocol}:{method}:{obfs}:{password}'.format(
            server=self._server,
            port=self._port,
            protocol=self._protocol,
            method=self._method,
            obfs=self._obfs,
            password=xbase64.encode(self._password, urlsafe=True))

        suffix_list = []
        if self._proto_param:
            suffix_list.append('protoparam={proto_param}'.format(
                proto_param=xbase64.encode(self.proto_param, urlsafe=True),
            ))

        if self._obfs_param:
            suffix_list.append('obfsparam={obfs_param}'.format(
                obfs_param=xbase64.encode(self.obfs_param, urlsafe=True),
            ))

        suffix_list.append('remarks={remarks}'.format(
            remarks=xbase64.encode(self.remarks, urlsafe=True),
        ))

        suffix_list.append('group={group}'.format(
            group=xbase64.encode(self.group, urlsafe=True),
        ))

        return 'ssr://{}'.format(xbase64.encode('{prefix}/?{suffix}'.format(
            prefix=prefix,
            suffix='&'.join(suffix_list),
        ), urlsafe=True))

    @url.setter
    def url(self, url: str):
        self.__reset_attributes()

        r = url.split('://')

        if r[0] == 'ssr':
            self.__parse_ssr(r[1])
        elif r[0] == 'ss':
            self.__parse_ss(r[1])

    def __parse_ssr(self, ssr_base64: str):
        ssr = ssr_base64.split('#')[0]
        ssr = xbase64.decode(ssr)

        if isinstance(ssr, bytes):
            return

        ssr_list = ssr.split(':')
        password_and_params = ssr_list[5].split('/?')

        self._server = ssr_list[0]
        self._port = int(ssr_list[1])
        self._protocol = ssr_list[2]
        self._method = ssr_list[3]
        self._obfs = ssr_list[4]
        self._password = xbase64.decode(password_and_params[0])

        params_dict = dict()
        for param in password_and_params[1].split('&'):
            param_list = param.split('=')
            params_dict[param_list[0]] = xbase64.decode(param_list[1])

        params_dict_keys = params_dict.keys()
        for key in ['proto_param', 'obfs_param', 'remarks', 'group']:
            tmp_key = key.replace('_', '')
            if tmp_key in params_dict_keys:
                setattr(self, '_{}'.format(key), params_dict[tmp_key])

    def __parse_ss(self, ss_base64: str):
        ss = ss_base64.split('#')
        if len(ss) > 1:
            self._remarks = urllib.parse.unquote(ss[1])
        ss = xbase64.decode(ss[0])

        if isinstance(ss, bytes):
            return

        # use split and join, in case of the password contains "@"/":"
        str_list = ss.split('@')

        server_and_port = str_list[-1].split(':')
        method_and_pass = '@'.join(str_list[0:-1]).split(':')

        self._server = server_and_port[0]
        self._port = int(server_and_port[1])
        self._method = method_and_pass[0]
        self._password = ':'.join(method_and_pass[1:])

    @property
    def plain(self):
        # check attributes
        if self.invalid_attributes:
            return None

        return '     server: {server}\n' \
               '       port: {port}\n' \
               '     method: {method}\n' \
               '   password: {password}\n' \
               '   protocol: {protocol}\n' \
               'proto_param: {proto_param}\n' \
               '       obfs: {obfs}\n' \
               ' obfs_param: {obfs_param}\n' \
               '    remarks: {remarks}\n' \
               '      group: {group}'.format(server=self.server,
                                             port=self.port,
                                             method=self.method,
                                             password=self.password,
                                             protocol=self.protocol,
                                             proto_param=self.proto_param,
                                             obfs=self.obfs,
                                             obfs_param=self.obfs_param,
                                             remarks=self.remarks,
                                             group=self.group,
                                             )

    @property
    def json_string(self):
        return self.get_json_string()

    def get_json_string(self, by_server_ip: bool = False):
        # check attributes
        if self.invalid_attributes:
            return None

        json_string = '{\n'

        if by_server_ip:
            json_string += '    "server": "{server}",\n'.format(server=self.server_ip)
        else:
            # by original server
            json_string += '    "server": "{server}",\n'.format(server=self.server)

        # other props
        json_string += '    "server_port": {server_port},\n' \
                       '    "method": "{method}",\n' \
                       '    "password": "{password}",\n' \
                       '    "protocol": "{protocol}",\n' \
                       '    "protocol_param": "{protocol_param}",\n' \
                       '    "obfs": "{obfs}",\n' \
                       '    "obfs_param": "{obfs_param}",\n\n' \
                       '    "local_address": "{local_address}",\n' \
                       '    "local_port": {local_port}' \
                       ''.format(server_port=self.port,
                                 method=self.method,
                                 password=self.password,
                                 protocol=self.protocol,
                                 protocol_param=self.proto_param,
                                 obfs=self.obfs,
                                 obfs_param=self.obfs_param,
                                 local_address=self.local_address,
                                 local_port=self.local_port,
                                 )
        json_string += '\n}'
        return json_string

    def generate_config_file(self, by_server_ip: bool = False):
        # check attributes
        if self.invalid_attributes:
            return None

        xp.about_t('Generating', self.path_to_config, 'config file')
        with open(self.path_to_config, 'wb') as f:
            f.write(self.get_json_string(by_server_ip=by_server_ip).encode('utf-8'))
            xp.success('Done.')

    @property
    def is_available(self):
        # check attributes
        if self.invalid_attributes:
            return None

        # check system
        if 'win32' == sys.platform:
            raise SystemNotSupportedException('Cannot use property `is_available` in windows.')

        # READY
        xp.job('CHECK AVAILABLE')

        self._path_to_config = os.path.join(tempfile.gettempdir(), 'ssr_utils_{time}.json'.format(
            time=str(time.time()).replace('.', '').ljust(17, '0'),
        ))

        # cmd
        self._cmd = '{python} {python_ssr} -c {path_to_config}'.format(
            python=os.getenv('PYTHON', '/usr/bin/python3'),
            python_ssr=os.getenv('PYTHON_SSR', '/repo/shadowsocksr/shadowsocks/local.py'),
            path_to_config=self.path_to_config,
        )

        # By server_ip
        self.generate_config_file(by_server_ip=True)

        if self.__check_available(hint='by IP'):
            self._server = self._server_ip
            self.__delete_config_file()
            print()
            return True

        # By server/domain
        if self.server_ip != self.server:
            self.generate_config_file()
            is_available = self.__check_available(hint='by Server/Domain')
            self.__delete_config_file()
            print()
            return is_available

        return False

    def __check_available(self, hint: str):
        xp.about_t('Start a sub progress of SSR', hint)

        # sub progress
        self._sub_progress = subprocess.Popen(
            self._cmd.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
        )

        # Group PID
        gpid = os.getpgid(self._sub_progress.pid)
        xp.wr(xp.Fore.LIGHTYELLOW_EX + '(G)PID {} '.format(gpid))

        # wait, during the progress launching.
        for i in range(0, 5):
            xp.wr(xp.Fore.LIGHTBLUE_EX + '.')
            xp.fi()
            time.sleep(1)
        xp.success(' Next.')

        # Request for IP
        my_ip = None
        try:
            xp.about_t('Try to request for the IP address')

            # socks5 proxy by SSR progress
            socks5_proxy = 'socks5://{local_address}:{local_port}'.format(
                local_address=self.local_address,
                local_port=self.local_port,
            )

            my_ip = requests.get(
                url='https://api.myip.com/',
                proxies={
                    'http': socks5_proxy,
                    'https': socks5_proxy,
                },
                timeout=15,
            ).json()

            xp.success('{} {}'.format(my_ip['ip'], my_ip['cc']))

        except Exception as e:
            # ConnectionError?
            xp.fx()
            xp.error(e)

        finally:
            xp.about_t('Kill SSR sub progress', 'PID {pid}'.format(pid=gpid))
            os.killpg(gpid, 9)
            xp.success('Done.')

        if my_ip:
            self._exit_ip = my_ip['ip']
            self._exit_country = my_ip['country']
            self._exit_country_code = my_ip['cc']
            return True

        return False

    def __request_for_exit_ip(self):
        return

    def __delete_config_file(self):
        xp.about_t('Deleting', self.path_to_config, 'config file')
        os.remove(self.path_to_config)
        xp.success('Done.')


def get_urls_by_subscribe(url: str,
                          cache_backend='sqlite',
                          cache_expire_after=300,
                          ):
    # request session
    request_session = requests_cache.core.CachedSession(
        cache_name=os.path.join(tempfile.gettempdir(), 'ssr_utils_cache'),
        backend=cache_backend,
        expire_after=cache_expire_after,
    )

    # request headers
    request_session.headers.update(
        {
            'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/71.0.3578.80 '
                          'Safari/537.36'
        }
    )

    # local proxies
    proxies = dict()

    # http proxy
    http_proxy = os.getenv('HTTP_PROXY', None)
    if http_proxy:
        proxies['http'] = http_proxy

    # https proxy
    https_proxy = os.getenv('HTTPS_PROXY', None)
    if https_proxy:
        proxies['https'] = https_proxy

    # {} => None
    if not proxies:
        proxies = None

    # get resp
    resp = request_session.get(url, proxies=proxies)
    if resp.status_code == 200:
        return get_urls_by_base64(resp.text)

    return list()


def get_urls_by_base64(text_base64: str):
    text = xbase64.decode(text_base64)
    if isinstance(text, str):
        return list_ext.remove_and_unique(text.split('\n'))
    return list()
