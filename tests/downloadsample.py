#!/usr/bin/env python
# encoding: utf-8

import sys
import os
import logging
import subprocess
import hashlib

import glob
import tempfile
import shutil

logger = logging.getLogger("nbt.tests.downloadsample")
workdir = os.path.dirname(__file__)
"""Directory for download and extracting the sample files"""
server_dir = os.path.join(workdir, 'Sample World')
server_jar_path = os.path.join(server_dir, 'server.jar')
# minecraft 1.20.2
# server_jar_url = 'https://piston-data.mojang.com/v1/objects/5b868151bd02b41319f54c8d4061b8cae84e665c/server.jar'
# server_jar_sha256_hex = '1daee4838569ad46e41f0a6f459684c500c7f2685356a40cfb7e838d6e78eae8'
# stop_command = b'/stop\n'
# minecraft 1.18.2
# server_jar_url = 'https://piston-data.mojang.com/v1/objects/c8f83c5655308435b3dcf03c06d9fe8740a77469/server.jar'
# server_jar_sha256_hex = '57be9d1e35aa91cfdfa246adb63a0ea11a946081e0464d08bc3d36651718a343'
# stop_command = b'/stop\n'
# minecraft 1.2.5
server_jar_url = 'https://launcher.mojang.com/v1/objects/d8321edc9470e56b8ad5c67bbd16beba25843336/server.jar'
server_jar_sha256_hex = '19285d7d16aee740f5a0584f0d80a4940f273a97f5a3eaf251fc1c6c3f2982d1'
stop_command = b'stop\n'
worlddir = os.path.join(server_dir, 'world')
"""Destination folder for the sample world."""


def download_with_external_tool(url, destination):
    """
    Download the file from the specified URL, and extract the contents.

    Uses the external curl program.
    wget fails if it is compiled with older version of OpenSSL. Hence we use curl.

    May raise an OSError (or one of it's subclasses).
    """
    logger.info("Downloading %s (with curl)" % url)
    # command = ['wget', '-O', destination, url]
    command = ['curl', '-o', destination, '-L', '-#', url]
    # Open a subprocess, wait till it is done, and get the STDOUT result
    exitcode = subprocess.call(command)
    if exitcode != 0:
        raise OSError("%s returned exit code %d" % (" ".join(command), exitcode))


def get_server_digest_ok():
    if os.path.exists(server_jar_path):
        with open(server_jar_path, 'rb') as f:
            current_sha256_hex = hashlib.sha256(f.read()).hexdigest()
    else:
        current_sha256_hex = None
    return current_sha256_hex == server_jar_sha256_hex


def install_server():
    if not get_server_digest_ok():
        download_with_external_tool(server_jar_url, server_jar_path)
        assert get_server_digest_ok()

    # fill in eula
    with open(os.path.join(server_dir, 'eula.txt'), 'wt') as f:
        # Well, is this even legal?
        f.write('eula=true\n')


def install():
    os.makedirs(server_dir, exist_ok=True)
    install_server()
    subprocess.run(
        ['java', '-jar', 'server.jar', 'nogui'],
        cwd=server_dir,
        input=stop_command,
        check=True,
        timeout=60,  # seconds
    )


def _mkdir(dstdir, subdir):
    """Helper function: create folder /dstdir/subdir"""
    os.mkdir(os.path.join(dstdir, os.path.normpath(subdir)))


def _copyglob(srcdir, destdir, pattern):
    """Helper function: copies files from /srcdir/pattern to /destdir/pattern.
    pattern is a glob pattern."""
    for fullpath in glob.glob(os.path.join(srcdir, os.path.normpath(pattern))):
        relpath = os.path.relpath(fullpath, srcdir)
        shutil.copy2(fullpath, os.path.join(destdir, relpath))


def _copyrename(srcdir, destdir, src, dest):
    """Helper function: copy file from /srcdir/src to /destdir/dest."""
    shutil.copy2(
        os.path.join(srcdir, os.path.normpath(src)),
        os.path.join(destdir, os.path.normpath(dest)),
    )


def temp_mcregion_world(worldfolder=worlddir):
    """Create a McRegion worldfolder in a temporary directory, based on the
    files in the given mixed worldfolder. Returns the temporary directory path."""
    tmpfolder = tempfile.mkdtemp(prefix="nbtmcregion")
    logger.info("Create temporary McRegion world folder at %s" % tmpfolder)
    return tmpfolder


def temp_anvil_world(worldfolder=worlddir):
    """Create a Anvil worldfolder in a temporary directory, based on the
    files in the given mixed worldfolder. Returns the temporary directory path."""
    tmpfolder = tempfile.mkdtemp(prefix="nbtanvil")
    logger.info("Create temporary Anvil world folder at %s" % tmpfolder)
    _mkdir(tmpfolder, 'region')
    _copyglob(worldfolder, tmpfolder, "region/*.mca")
    _copyrename(worldfolder, tmpfolder, "level.dat", "level.dat")
    return tmpfolder


def cleanup_temp_world(tmpfolder):
    """Remove a temporary directory"""
    logger.info("Remove temporary world folder at %s" % tmpfolder)
    shutil.rmtree(tmpfolder, ignore_errors=True)


if __name__ == '__main__':
    if len(logger.handlers) == 0:
        # Logging is not yet configured. Configure it.
        logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(levelname)-8s %(message)s')
    success = install()
    sys.exit(0 if success else 1)
