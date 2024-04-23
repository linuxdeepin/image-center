#!/usr/bin/env python3
# _*_ coding:utf-8 _*_

# SPDX-FileCopyrightText: 2023 UnionTech Software Technology Co., Ltd.

# SPDX-License-Identifier: Apache Software License
import os

from image_center import ImageCenter

current_dir = os.path.dirname(os.path.abspath(__file__))


def test_client():
    res = ImageCenter.find_image(f"{current_dir}/test.png")
    assert res