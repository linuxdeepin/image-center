#!/usr/bin/env python3
# _*_ coding:utf-8 _*_

# SPDX-FileCopyrightText: 2023 UnionTech Software Technology Co., Ltd.

# SPDX-License-Identifier: Apache Software License
import enum
import os
import platform
import tempfile
from os import popen


@enum.unique
class DisplayServer(enum.Enum):
    wayland = "wayland"
    x11 = "x11"


@enum.unique
class PlatForm(enum.Enum):
    win = "Windows"
    linux = "Linux"
    macos = "Darwin"


class _Setting:
    """配置模块"""

    SERVER_IP = "127.0.0.1"
    PORT = 8889
    NETWORK_RETRY = 1
    PAUSE = 1
    TIMEOUT = 5
    MAX_MATCH_NUMBER = 100

    IS_LINUX = False
    IS_WINDOWS = False
    IS_MACOS = False

    PIC_PATH = ""
    IMAGE_RATE = 0.9
    # Win default path——C:\\Users\\xxxx\\AppData\\Local\\Temp
    # Linux_MacOS default path——/tmp/screen.png
    SCREEN_CACHE = os.path.join(tempfile.gettempdir(), 'screen.png')
    TMPDIR = os.path.join(tempfile.gettempdir(), 'tmpdir')
    # IMAGE_MATCH_NUMBER = 1
    # IMAGE_MATCH_WAIT_TIME = 1

    if platform.system() == PlatForm.win.value:
        # windows
        IS_WINDOWS = True
    elif platform.system() == PlatForm.macos.value:
        # MacOS
        IS_MACOS = True
    elif platform.system() == PlatForm.linux.value:
        # Linux
        IS_LINUX = True
        # 显示服务器
        DISPLAY_SERVER = (
                             popen("cat ~/.xsession-errors | grep XDG_SESSION_TYPE | head -n 1")
                             .read()
                             .split("=")[-1]
                             .strip("\n")
                         ) or ("x11" if popen("ps -ef | grep -v grep | grep kwin_x11").read() else "wayland")

        IS_X11 = DISPLAY_SERVER == DisplayServer.x11.value
        IS_WAYLAND = DISPLAY_SERVER == DisplayServer.wayland.value


setting = _Setting()
