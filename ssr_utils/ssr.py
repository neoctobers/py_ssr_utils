# coding:utf-8
import time
import xbase64
import xprint as xp


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

        self._local_address = None
        self._local_port = None
        self._path_to_config = None

        self._ip = None
        self._country = None
        self._country_code = None
        pass

    def __reset_server(self):
        self._server = ''
        self._port = 443
        self._method = ''
        self._password = ''
        self._protocol = 'origin'
        self._proto_param = ''
        self._obfs = 'plain'
        self._obfs_param = ''

    @property
    def remarks(self):
        return self._remarks or 'Generate by PyPI: ssr-utils.url'

    @remarks.setter
    def remarks(self, value: str):
        self._remarks = value

    @property
    def group(self):
        return self._group or 'PyPI: ssr-utils'

    @group.setter
    def group(self, value: str):
        self._group = value

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
        return self._path_to_config or 'ssr-config.json'

    @path_to_config.setter
    def path_to_config(self, value: str):
        self._path_to_config = value

    @property
    def _requests_proxies(self):
        return {
            'http': 'socks5://{local_address}:{local_port}'.format(
                local_address=self.local_address,
                local_port=self.local_port,
            ),
            'https': 'socks5://{local_address}:{local_port}'.format(
                local_address=self.local_address,
                local_port=self.local_port,
            ),
        }

    @property
    def ip(self):
        return self._ip

    @property
    def country(self):
        return self._country

    @property
    def country_code(self):
        return self._country_code

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
        if not self._server:
            xp.error('server not set.')
            return None

        return {
            'server': self._server,
            '_port': self._port,
            '_method': self._method,
            '_password': self._password,
            '_protocol': self._protocol,
            '_proto_param': self._proto_param,
            '_obfs': self._obfs,
            '_obfs_param': self._obfs_param,

            '_remarks': self.remarks,
            '_group': self.group,
        }

    @property
    def url(self):
        if not self._server:
            xp.error('server not set.')
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
                proto_param=xbase64.encode(self._proto_param, urlsafe=True),
            ))

        if self._obfs_param:
            suffix_list.append('obfsparam={obfs_param}'.format(
                obfs_param=xbase64.encode(self._obfs_param, urlsafe=True),
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
        self.__reset_server()

        r = url.split('://')

        if r[0] == 'ssr':
            self.__parse_ssr(r[1])
        elif r[0] == 'ss':
            self.__parse_ss(r[1])

    def __parse_ssr(self, ssr_base64: str):
        ssr = xbase64.decode(ssr_base64)
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
                setattr(self, key, params_dict[tmp_key])

    def __parse_ss(self, ss_base64: str):
        ss = xbase64.decode(ss_base64)
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
        if not self._server:
            xp.error('server not set.')
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
               '      group: {group}'.format(server=self._server,
                                             port=self._port,
                                             method=self._method,
                                             password=self._password,
                                             protocol=self._protocol,
                                             proto_param=self._proto_param,
                                             obfs=self._obfs,
                                             obfs_param=self._obfs_param,
                                             remarks=self.remarks,
                                             group=self.group,
                                             )

    @property
    def json_string(self):
        if not self._server:
            xp.error('server not set.')
            return None

        json_string = '{\n'
        json_string += '    "server": "{server}",\n' \
                       '    "server_port": {server_port},\n' \
                       '    "method": "{method}",\n' \
                       '    "password": "{password}",\n' \
                       '    "protocol": "{protocol}",\n' \
                       '    "protocol_param": "{protocol_param}",\n' \
                       '    "obfs": "{obfs}",\n' \
                       '    "obfs_param": "{obfs_param}",\n\n' \
                       '    "local_address": "{local_address}",\n' \
                       '    "local_port": {local_port}' \
                       ''.format(server=self._server,
                                 server_port=self._port,
                                 method=self._method,
                                 password=self._password,
                                 protocol=self._protocol,
                                 protocol_param=self._proto_param,
                                 obfs=self._obfs,
                                 obfs_param=self._obfs_param,
                                 local_address=self.local_address,
                                 local_port=self.local_port,
                                 )
        json_string += '\n}'
        return json_string

    def generate_config_file(self):
        if not self._server:
            xp.error('server not set.')
            return

        xp.about_t('Generating', self.path_to_config, 'config file')
        with open(self.path_to_config, 'wb') as f:
            f.write(self.json_string.encode('utf-8'))
            xp.success('Done.')

    @property
    def is_available(self):
        import os
        import dotenv
        import tempfile
        import requests
        import subprocess

        if not self._server:
            xp.error('server not set.')
            return None

        xp.job('CHECK AVAILABLE')

        self._path_to_config = os.path.join(tempfile.gettempdir(), 'ssr_utils_{time}.json'.format(
            time=str(time.time()).replace('.', '').ljust(17, '0'),
        ))

        # config file
        self.generate_config_file()

        # cmd
        dotenv.load_dotenv()
        cmd = '{python} {python_ssr} -c {path_to_config}'.format(
            python=os.getenv('PYTHON', '/usr/bin/python3'),
            python_ssr=os.getenv('PYTHON_SSR', '/repo/shadowsocksr/shadowsocks/local.py'),
            path_to_config=self.path_to_config,
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

        my_ip = None
        try:
            xp.about_t('Try to request for the IP address')
            my_ip = requests.get(
                url='https://api.myip.com/',
                proxies=self._requests_proxies,
                timeout=15,
            ).json()
            xp.success(my_ip['ip'])

        except ConnectionError:
            xp.fx()
            xp.error('A proxy error occurred.')
            xp.error('A proxy error occurred.')
            xp.error('A proxy error occurred.')

        except Exception as e:
            xp.fx()
            xp.error(e)

        finally:
            gpid = os.getpgid(sub_progress_of_ssr.pid)

            xp.about_t('Kill SSR sub progress', 'PID {pid}'.format(pid=gpid))
            os.killpg(gpid, 9)
            xp.success('Done.')

            xp.about_t('Deleting', self.path_to_config, 'config file')
            os.remove(self.path_to_config)
            xp.success('Done.')

        if my_ip:
            xp.success('AVAILABLE')
            xp.fx()

            self._ip = my_ip['ip']
            self._country = my_ip['country']
            self._country_code = my_ip['cc']
            return True

        return False


def get_ssr_urls_by_subscribe(url: str,
                              cache_backend='sqlite',
                              cache_expire_after=300,
                              ):
    import os
    import tempfile
    import requests_cache
    import list_ext

    r = requests_cache.core.CachedSession(
        cache_name=os.path.join(tempfile.gettempdir(), 'ssr_utils_cache'),
        backend=cache_backend,
        expire_after=cache_expire_after,
    ).get(url)

    # success
    if r.status_code == 200:
        return list_ext.sur(xbase64.decode(r.text).split('\n'))

    return list()

