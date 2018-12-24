# coding:utf-8
import os
import sys
import time
import socket
import requests
import requests_cache
import list_ext
import subprocess
import profig
import tempfile
import common_patterns
import xprint as xp
import xbase64
import urllib.parse
import proxychains_conf_generator
from .errors import *


class SSR:
    def __init__(self, path_to_config='config.ini'):
        self._cfg = profig.Config(path_to_config)
        self._cfg.init('path.python', '/usr/bin/python3')
        self._cfg.init('path.python_ssr', '/data/repo/shadowsocksr/shadowsocks/local.py')
        self._cfg.init('path.proxychains4', '/usr/local/bin/porxychains4')
        self._cfg.init('ssr_utils.proxychains4_cache_time', 300)
        self._cfg.init('ssr_utils.proxy_file', 'proxy.txt')
        self._cfg.sync()

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
        self._path_to_config_file = None

        self._exit_ip = None
        self._exit_country = None
        self._exit_country_code = None

        self._cmd = None
        self._cmd_prefix = None
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
        self._path_to_config_file = None

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
    def path_to_config_file(self):
        return self._path_to_config_file or os.path.join(os.getcwd(), 'shadowsocksr-config.json')

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
    def pc4_conf_file(self):
        if os.path.exists(self._cfg['ssr_utils.proxy_file']):
            path_to_pc4_conf_file = os.path.join(tempfile.gettempdir(), 'ssr_utils_pc4.conf')

            if os.path.exists(path_to_pc4_conf_file) and \
                    time.time() - os.stat(path_to_pc4_conf_file).st_mtime \
                    < self._cfg['ssr_utils.proxychains4_cache_time']:
                return path_to_pc4_conf_file

            xp.job('Make a local proxy chain from "proxy.txt"')
            for line in open(self._cfg['ssr_utils.proxy_file']).readlines():
                line = line.strip('\n')
                # proxy_expression
                proxy = list_ext.remove(line.split(' '))
                proxy_expression = '{protocol}://'.format(protocol=proxy[0])
                if 5 <= len(proxy):
                    proxy_expression += '{username}:{password}@'.format(username=proxy[3], password=proxy[4])
                proxy_expression += '{host}:{port}'.format(host=proxy[1], port=proxy[2])

                # pc4_conf_file
                requests_proxies = {
                    'http': proxy_expression,
                    'https': proxy_expression,
                }

                # try to get IP
                try:
                    r = requests.get(url='https://api.myip.com', proxies=requests_proxies)
                    if 200 == r.status_code:
                        # pc4
                        g = proxychains_conf_generator.Generator(
                            proxy=line,
                            quiet_mode=True,
                        )
                        return g.write(path_to_conf=path_to_pc4_conf_file)

                except Exception as e:
                    xp.error(e)
                    pass

            xp.error('No available proxy in "{}". Remove it if do not need a proxy.'.format(
                self._cfg['ssr_utils.proxy_file'],
            ))
            xp.ex()

        return None

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
            if not getattr(self, key):
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
            'proto_param': None,
            'obfs': 'plain',
            'obfs_param': None,

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
    def config_json_string(self):
        return self.get_config_json_string()

    def get_config_json_string(self, by_ip: bool = False):
        # check attributes
        if self.invalid_attributes:
            return None

        configs = list()

        # by: ip / server
        if by_ip:
            configs.append('"server": "{}",'.format(self.server_ip))
        else:
            configs.append('"server": "{}",'.format(self.server))

        configs.append('"server_port": {},'.format(self.port))
        configs.append('"method": "{}",'.format(self.method))
        configs.append('"password": "{}",'.format(self.password))
        configs.append('"protocol": "{}",'.format(self.protocol))
        configs.append('"protocol_param": "{}",'.format(self.proto_param))
        configs.append('"obfs": "{}",'.format(self.obfs))
        configs.append('"obfs_param": "{}",'.format(self.obfs_param))
        configs.append('"local_address": "{}",'.format(self.local_address))
        configs.append('"local_port": {}'.format(self.local_port))

        return '{\n' + '\n'.join(configs) + '\n}'

    def write_config_file(self, path_to_file=None, by_ip: bool = False, plain_to_console: bool = False):
        # check attributes
        if self.invalid_attributes:
            return None

        if path_to_file:
            self._path_to_config_file = path_to_file

        xp.about_t('Generating', self.path_to_config_file, 'for shadowsocksr')
        with open(self.path_to_config_file, 'wb') as f:
            json_string = self.get_config_json_string(by_ip=by_ip)
            f.write(json_string.encode('utf-8'))
            xp.success()
            if plain_to_console:
                xp.plain_text(json_string)

    @property
    def is_available(self):
        return self.get_available()

    def get_available(self):
        if self.invalid_attributes:
            return None

        # check system
        if 'win32' == sys.platform:
            raise SystemNotSupportedException('Cannot use property `is_available` in windows.')

        # READY
        xp.job('CHECK AVAILABLE')

        self._path_to_config_file = os.path.join(tempfile.gettempdir(), 'ssr_utils_{time}.json'.format(
            time=str(time.time()).replace('.', '').ljust(17, '0'),
        ))

        # cmd with pc4
        pc4_conf_file = self.pc4_conf_file
        if pc4_conf_file:
            self._cmd = '{path_to_pc4} -q -f {pc4_conf_file} '.format(
                path_to_pc4=self._cfg['path.proxychains4'],
                pc4_conf_file=pc4_conf_file,
            )
        else:
            self._cmd = ''

        # Python SSR
        self._cmd += '{python} {python_ssr} -c {path_to_config}'.format(
            python=self._cfg['path.python'],
            python_ssr=self._cfg['path.python_ssr'],
            path_to_config=self.path_to_config_file,
        )

        # By server_ip
        self.write_config_file(by_ip=True)

        if self.__check_available(hint='by IP'):
            self._server = self._server_ip
            self.__check_finished()
            print()
            return True

        # By server/domain
        if self.server_ip != self.server:
            self.write_config_file()
            is_available = self.__check_available(hint='by Server/Domain')
            self.__check_finished()
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

    def __check_finished(self):
        xp.about_t('Deleting', self.path_to_config_file, 'config file')
        os.remove(self.path_to_config_file)
        xp.success()


def get_urls_by_subscribe(url: str,
                          cache_backend='sqlite',
                          cache_expire_after=300,
                          request_proxies=None,
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

    # get resp
    resp = request_session.get(url, proxies=request_proxies)
    if resp.status_code == 200:
        return get_urls_by_base64(resp.text)

    return list()


def get_urls_by_base64(text_base64: str):
    text = xbase64.decode(text_base64)
    if isinstance(text, str):
        return list_ext.remove_and_unique(text.split('\n'))
    return list()
