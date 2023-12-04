# setup.py

from setuptools import setup

setup(
    name="tfs-linker",
    version="0.1",
    packages=["tfs_linker"],
    package_data={
        "tfs_linker": ["*.xml"],
    },
    entry_points={
        "console_scripts": [
            "tfs-linker = tfs_linker:run_linker",
            "tfs-linker-auto-config = tfs_linker:configure_idea",
        ],
    },
)
