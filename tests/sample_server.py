import hashlib
import os
import stat
import subprocess
from concurrent.futures import ThreadPoolExecutor

from .downloadsample import download_with_external_tool

servers_dir = os.path.join('tests', 'sample_server')

versions = {
    '1.20.2': {
        'server_jar_url': 'https://piston-data.mojang.com/v1/objects/5b868151bd02b41319f54c8d4061b8cae84e665c/server.jar',
        'server_jar_sha256_hex': '1daee4838569ad46e41f0a6f459684c500c7f2685356a40cfb7e838d6e78eae8',
        'stop_command': b'/stop\n',
        'port': 25565,
    },
    '1.19.4': {
        'server_jar_url': 'https://piston-data.mojang.com/v1/objects/8f3112a1049751cc472ec13e397eade5336ca7ae/server.jar',
        'server_jar_sha256_hex': 'a524a10da550741785c8c3a0fb39047f106b0c7c2cfa255e8278cb6f1abe3f53',
        'stop_command': b'/stop\n',
        'port': 25564,
    },
    '1.18.2': {
        'server_jar_url': 'https://piston-data.mojang.com/v1/objects/c8f83c5655308435b3dcf03c06d9fe8740a77469/server.jar',
        'server_jar_sha256_hex': '57be9d1e35aa91cfdfa246adb63a0ea11a946081e0464d08bc3d36651718a343',
        'stop_command': b'/stop\n',
        'port': 25563,
    },
    '1.17.1': {
        'server_jar_url': 'https://piston-data.mojang.com/v1/objects/a16d67e5807f57fc4e550299cf20226194497dc2/server.jar',
        'server_jar_sha256_hex': 'e8c211b41317a9f5a780c98a89592ecb72eb39a6e475d4ac9657e5bc9ffaf55f',
        'stop_command': b'/stop\n',
        'port': 25562,
    },
    '1.16.5': {
        'server_jar_url': 'https://piston-data.mojang.com/v1/objects/1b557e7b033b583cd9f66746b7a9ab1ec1673ced/server.jar',
        'server_jar_sha256_hex': '58f329c7d2696526f948470aa6fd0b45545039b64cb75015e64c12194b373da6',
        'stop_command': b'/stop\n',
        'port': 25561,
    },
    '1.15.2': {
        'server_jar_url': 'https://piston-data.mojang.com/v1/objects/bb2b6b1aefcd70dfd1892149ac3a215f6c636b07/server.jar',
        'server_jar_sha256_hex': '80cf86dc2004ec6a2dc0183d1c75a9af3ba0669f7c332e4247afb1d76fb67e8a',
        'stop_command': b'/stop\n',
        'port': 25560,
    },
    '1.14.4': {
        'server_jar_url': 'https://piston-data.mojang.com/v1/objects/3dc3d84a581f14691199cf6831b71ed1296a9fdf/server.jar',
        'server_jar_sha256_hex': '5ecdedab3a6e129321a444490d0a467c25ea702a24a99cebe3b6aed41f8f5729',
        'stop_command': b'/stop\n',
        'port': 25559,
    },
    '1.13.2': {
        'server_jar_url': 'https://piston-data.mojang.com/v1/objects/3737db93722a9e39eeada7c27e7aca28b144ffa7/server.jar',
        'server_jar_sha256_hex': 'ffd3aa2c25c5ba68a706b59f2abdc69ac1748e115ca9d3b47941e197736f088e',
        'stop_command': b'/stop\n',
        'port': 25558,
    },
    '1.12.2': {
        'server_jar_url': 'https://piston-data.mojang.com/v1/objects/886945bfb2b978778c3a0288fd7fab09d315b25f/server.jar',
        'server_jar_sha256_hex': 'fe1f9274e6dad9191bf6e6e8e36ee6ebc737f373603df0946aafcded0d53167e',
        'stop_command': b'/stop\n',
        'port': 25557,
    },
    '1.11.2': {
        'server_jar_url': 'https://piston-data.mojang.com/v1/objects/f00c294a1576e03fddcac777c3cf4c7d404c4ba4/server.jar',
        'server_jar_sha256_hex': 'dec47d36b429fd05076b90b1f42c2a25138bc39204aa51b9674ef2a98d64d88a',
        'stop_command': b'/stop\n',
        'port': 25556,
    },
    '1.10.2': {
        'server_jar_url': 'https://piston-data.mojang.com/v1/objects/3d501b23df53c548254f5e3f66492d178a48db63/server.jar',
        'server_jar_sha256_hex': '195f468227c5f9218f3919538b9b16ba34adced67fc7d7b652c508a5e8d07a21',
        'stop_command': b'/stop\n',
        'port': 25555,
    },
    '1.9.4': {
        'server_jar_url': 'https://piston-data.mojang.com/v1/objects/edbb7b1758af33d365bf835eb9d13de005b1e274/server.jar',
        'server_jar_sha256_hex': '13fea7aa10d804dd14ed7ebde2493dc64c7d3c8173369309bd7f6ea4c0ea40ad',
        'stop_command': b'/stop\n',
        'port': 25554,
    },
}

latest_version = '1.20.2'


def get_world_dir(version=latest_version):
    server_dir = os.path.join(servers_dir, version)
    world_dir = os.path.join(server_dir, 'world')

    if not os.path.exists(world_dir):
        os.makedirs(server_dir, exist_ok=True)
        start_server(server_dir, version)
        assert os.path.exists(world_dir)
        mark_readonly(server_dir)

    return world_dir


def start_server(server_dir, version):
    install_server(server_dir, version)
    subprocess.run(
        ['java', '-jar', 'server.jar', 'nogui'],
        cwd=server_dir,
        input=versions[version]['stop_command'],
        check=True,
        timeout=120,  # seconds
    )


def install_server(server_dir, version):
    server_jar_path = os.path.join(server_dir, 'server.jar')
    server_jar_url = versions[version]['server_jar_url']
    server_jar_sha256_hex = versions[version]['server_jar_sha256_hex']

    ensure_downloaded(server_jar_path, server_jar_sha256_hex, server_jar_url)

    # fill in eula
    with open(os.path.join(server_dir, 'eula.txt'), 'wt') as f:
        # Well, is this even legal?
        f.write('eula=true\n')

    # configure server.properties
    with open(os.path.join(server_dir, 'server.properties'), 'wt') as f:
        f.write('level-seed=testseed\n')
        f.write(f'server-port={versions[version]["port"]}\n')
        f.write('server-ip=127.0.0.1\n')


def mark_readonly(directory):
    permission_mask = (
        stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH |
        stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    )
    for root, dirs, files in os.walk(directory):
        for d in dirs:
            current_mode = os.stat(os.path.join(root, d)).st_mode
            os.chmod(os.path.join(root, d), current_mode & permission_mask)
        for f in files:
            current_mode = os.stat(os.path.join(root, f)).st_mode
            os.chmod(os.path.join(root, f), current_mode & permission_mask)
    current_mode = os.stat(directory).st_mode
    os.chmod(directory, current_mode & permission_mask)


def ensure_downloaded(local_path, sha256_hex, url):
    if get_sha256_hex(local_path) != sha256_hex:
        download_with_external_tool(url, local_path)
        real_sha256_hex = get_sha256_hex(local_path)
        assert real_sha256_hex == sha256_hex, f'file {local_path}: expected digest {sha256_hex}, got {real_sha256_hex}'


def get_sha256_hex(path):
    if not os.path.exists(path):
        return None
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def ensure_all():
    with ThreadPoolExecutor(max_workers=2) as executor:
        for version in versions.keys():
            executor.submit(get_world_dir, version)


if __name__ == '__main__':
    ensure_all()
