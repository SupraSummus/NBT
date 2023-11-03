import os

import pytest

from nbt.world import WorldFolder

from .sample_server import get_world_dir, versions


@pytest.fixture(
    scope='session',
    autouse=True,
    params=versions.keys(),
)
def world_dir(request):
    yield get_world_dir(version=request.param)


def test_we_have_a_world_dir(world_dir):
    assert os.path.isdir(world_dir)
    assert os.path.exists(os.path.join(world_dir, 'level.dat'))


def test_read_no_smoke(world_dir):
    """We dont crash when reading a world"""
    world = WorldFolder(world_dir)
    assert world.chunk_count()

    bb = world.get_boundingbox()
    center_x = (bb.minx + bb.maxx) // 2
    center_z = (bb.minz + bb.maxz) // 2
    chunk = world.get_chunk(center_x, center_z)
    assert chunk.get_max_height()

    block = chunk.get_block(0, 0, 0)
    assert block
