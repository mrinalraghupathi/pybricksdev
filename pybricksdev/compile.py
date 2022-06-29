# SPDX-License-Identifier: MIT
# Copyright (c) 2019-2022 The Pybricks Authors

import asyncio
import logging
import os
from typing import List, Optional

import mpy_cross_v5

from .tools import chunk

logger = logging.getLogger(__name__)

BUILD_DIR = "build"
TMP_PY_SCRIPT = "_tmp.py"
TMP_MPY_SCRIPT = "_tmp.mpy"


def make_build_dir():
    # Create build folder if it does not exist
    if not os.path.exists(BUILD_DIR):
        os.mkdir(BUILD_DIR)

    # Raise error if there happens to be a file by this name
    if os.path.isfile(BUILD_DIR):
        raise FileExistsError("A file named build already exists.")


async def compile_file(path: str, abi: int, compile_args: Optional[List[str]] = None):
    """Compiles a Python file with ``mpy-cross``.

    Arguments:
        path:
            Path to script that is to be compiled.
        abi:
            Expected MPY ABI version.
        compile_args:
            Extra arguments for ``mpy-cross``.

    Returns:
        The compiled script in MPY format.

    Raises:
        RuntimeError: if there is not a running event loop.
        ValueError if MPY ABI version is not 5.
        subprocess.CalledProcessError: if executing the ``mpy-cross` tool failed.
    """

    # Get version info
    with open(path, "r") as f:
        if abi == 5:
            loop = asyncio.get_running_loop()

            proc, mpy = await loop.run_in_executor(
                None,
                lambda: mpy_cross_v5.mpy_cross_compile(
                    path, f.read(), no_unicode=True, extra_args=compile_args
                ),
            )

            proc.check_returncode()

            return mpy
        else:
            raise ValueError("mpy_version must be 5")


def save_script(py_string):
    """Save a MicroPython one-liner to a file."""
    # Make the build directory.
    make_build_dir()

    # Path to temporary file.
    py_path = os.path.join(BUILD_DIR, TMP_PY_SCRIPT)

    # Write Python command to a file.
    with open(py_path, "w") as f:
        f.write(py_string)
        f.write("\n")

    # Return path to file
    return py_path


def print_mpy(data):
    # Print as string as a sanity check.
    print()
    print("Bytes:")
    print(data)

    # Print the bytes as a C byte array for development of new MicroPython
    # ports without usable I/O, REPL or otherwise.
    WIDTH = 8
    print()
    print(f"// MPY file. Version: {data[1]}. Size: {len(data)} bytes")
    print("const uint8_t script[] = {")

    for c in chunk(data, WIDTH):
        hex_repr = [f"0x{i:02X}" for i in c]
        print(f"    {', '.join(hex_repr)},")

    print("};")
