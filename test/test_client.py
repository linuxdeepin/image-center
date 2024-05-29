#!/usr/bin/env python3
# _*_ coding:utf-8 _*_

# SPDX-FileCopyrightText: 2023 UnionTech Software Technology Co., Ltd.

# SPDX-License-Identifier: Apache Software License
import os

from image_center import ImageCenter

current_dir = os.path.dirname(os.path.abspath(__file__))


def test_client_png():
    res = ImageCenter.find_image(f"{current_dir}/test.png")
    assert res


def test_client_png_to():
    res = ImageCenter.find_image(f"{current_dir}/test")
    assert res


def test_client_jpg():
    res = ImageCenter.find_image(f"{current_dir}/test1.jpg")
    assert res


def test_client_jpg_to():
    res = ImageCenter.find_image(f"{current_dir}/test1")
    assert res


def test_client_jpeg():
    res = ImageCenter.find_image(f"{current_dir}/test2.jpeg")
    assert res


def test_client_jpeg_to():
    res = ImageCenter.find_image(f"{current_dir}/test2")
    assert res

if __name__ == "__main__":
    test_client_png()
    test_client_png_to()
    test_client_jpg()
    test_client_jpg_to()
    test_client_jpeg()
    test_client_jpeg_to()