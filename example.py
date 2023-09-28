#!/usr/bin/env python3
# _*_ coding:utf-8 _*_

# SPDX-FileCopyrightText: 2023 UnionTech Software Technology Co., Ltd.

# SPDX-License-Identifier: Apache Software License
from image_center.server import server
from image_center.conf import setting

setting.PORT = 8889  # 默认端口是8889，可以修改为其他端口；

server()