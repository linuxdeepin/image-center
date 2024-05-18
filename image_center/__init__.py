#!/usr/bin/env python3
# _*_ coding:utf-8 _*_

# SPDX-FileCopyrightText: 2023 UnionTech Software Technology Co., Ltd.

# SPDX-License-Identifier: Apache Software License
import logging
import os
import random
import time
from typing import List, Union
from xmlrpc.client import Binary
from xmlrpc.client import ServerProxy

import easyprocess

try:
    import cv2 as cv
    import numpy as np

    GET_OPENCV_FORM_RPC = False
except ModuleNotFoundError:
    GET_OPENCV_FORM_RPC = True

try:
    import pyscreenshot
    from PIL import Image
except ModuleNotFoundError:
    pass

from image_center.conf import setting

logger = logging.getLogger("image_center")


class TemplateElementNotFound(BaseException):
    """通过模板资源未匹配到对应元素"""

    def __init__(self, *name):
        """
        通过模板资源未匹配到对应元素
        :param name: 命令
        """
        err = f"通过图片资源, 未在屏幕上匹配到元素"
        template = [f"{i}.png" for i in name]
        BaseException.__init__(self, err, *template)


class TemplatePictureNotExist(BaseException):
    """图片资源，文件不存在"""

    def __init__(self, name):
        """
        文件不存在
        :param name: 命令
        """
        err = f"图片资源：{name} 文件不存在!"
        logger.error(err)
        BaseException.__init__(self, err)


class ImageCenter:
    """图像识别的工具类"""

    wayland_screen_dbus = "qdbus org.kde.KWin /Screenshot screenshotFullscreen"

    @classmethod
    def _match_image_by_opencv(
            cls,
            image_path: str,
            rate: float = None,
            multiple: bool = False,
            picture_abspath: str = None,
            screen_bbox: List[int] = None,
            log_level: str = "info",
            network_retry: int = 1,
    ):
        """
         图像识别，匹配小图在屏幕中的坐标 x, y，当前仅支持1个主屏幕，如果存在多个屏幕只会截取主屏幕内容。
        :param image_path: 图像识别目标文件的存放路径
        :param rate: 匹配度
        :param multiple: 是否返回匹配到的多个目标
        :param picture_abspath: 大图，默认大图是截取屏幕，否则使用传入的图片；
        :param screen_bbox: 截取屏幕上指定区域图片（仅支持X11下使用）；
            [x, y, w, h]
            x: 左上角横坐标；y: 左上角纵坐标；w: 宽度；h: 高度；根据匹配度返回坐标
        :param network_retry: 连接服务器重试次数
        """
        # pylint: disable=I1101,E1101
        if rate is None:
            rate = float(setting.IMAGE_RATE)
        screen = setting.SCREEN_CACHE

        if not picture_abspath:
            if screen_bbox:
                screen = cls.save_temporary_picture(*screen_bbox) + ".png"
            else:
                if setting.IS_X11:
                    try:
                        pyscreenshot.grab().save(screen)
                    except easyprocess.EasyProcessError:
                        ...
                elif setting.IS_WAYLAND:
                    screen = os.popen(cls.wayland_screen_dbus).read().strip("\n")
                else:
                    #for windows and macos
                    pyscreenshot.grab().save(screen)

        else:
            screen = picture_abspath
        if os.name == 'nt':  # Windows
            template_path = os.path.expanduser(image_path)
        else:  # Linux and MacOS
            template_path = os.path.expanduser(f"{image_path}")
        if GET_OPENCV_FORM_RPC:
            server = ServerProxy(f"http://{setting.SERVER_IP}:{setting.PORT}", allow_none=True)
            # pylint: disable=consider-using-with
            screen_rb = open(screen, "rb")
            # pylint: disable=consider-using-with
            template_rb = open(template_path, "rb")
            for _ in range(network_retry + 1):
                try:
                    screen_path = server.image_put(Binary(screen_rb.read()))
                    screen_rb.close()
                    tpl_path = server.image_put(Binary(template_rb.read()))
                    template_rb.close()
                    return server.match_image_by_opencv(
                        tpl_path, screen_path, rate, multiple
                    )
                except OSError as exc:
                    raise EnvironmentError(
                        f"OCR 服务器链接失败. http://{setting.SERVER_IP}:{setting.PORT}"
                    ) from exc
        else:
            if not os.path.exists(template_path):
                raise TemplatePictureNotExist(template_path)
            screen = cv.imread(screen)
            template = cv.imread(template_path)
            result = cv.matchTemplate(screen, template, cv.TM_CCOEFF_NORMED)
            if not multiple:
                pos_start = cv.minMaxLoc(result)[3]
                _x = int(pos_start[0]) + int(template.shape[1] / 2)
                _y = int(pos_start[1]) + int(template.shape[0] / 2)
                similarity = cv.minMaxLoc(result)[1]
                tmp_log = (
                    f"***{template_path[-40:]}"
                    if len(template_path) >= 40
                    else template_path
                )
                if similarity < rate:
                    getattr(logger, log_level)(f"{tmp_log} | 相似度:{round(similarity * 100, 2)}% ")
                    return False
                if screen_bbox:
                    bbox_x, bbox_y, *_ = screen_bbox
                    _x = bbox_x + _x
                    _y = bbox_y + _y
                getattr(logger, log_level)(
                    f"{tmp_log} | 坐标:{_x, _y} | 相似度:{round(similarity * 100, 2)}%"
                )
                return _x, _y
            # multiple = True
            loc = np.where(result >= rate)
            tmp_list_out = []
            tmp_list_in = []
            loc_list = list(zip(*loc))
            for i in range(0, len(loc_list) - 1):
                tmp_list_in.append(loc_list[i])
                if (
                        loc_list[i + 1][0] != loc_list[i][0]
                        or (loc_list[i + 1][1] - loc_list[i][1]) > 1
                ):
                    tmp_list_out.append(tmp_list_in)
                    tmp_list_in = []
                    continue
                if i == len(loc_list) - 2:
                    tmp_list_in.append(loc_list[-1])
                    tmp_list_out.append(tmp_list_in)
            result_list = []
            x_list, y_list = [], []
            if tmp_list_out:
                for i in tmp_list_out:
                    for j in i:
                        x_list.append(j[1])
                        y_list.append(j[0])
                    _x = np.mean(x_list) + int(template.shape[1] / 2)
                    _y = np.mean(y_list) + int(template.shape[0] / 2)
                    result_list.append((_x, _y))
                    x_list, y_list = [], []
                result_list.sort(key=lambda x: x[0])
                return result_list
            return False

    @classmethod
    def save_temporary_picture(cls, _x: int, _y: int, width: int, height: int, log_level="info"):
        """
         截取屏幕上指定区域图片，保存临时图片，并返回图片路径
        :param _x: 左上角横坐标
        :param _y: 左上角纵坐标
        :param width: 宽度
        :param height: 高度
        :param log_level: 日志级别
        :return: 图片路径
        """
        # pylint: disable=I1101,E1101
        if not os.path.exists(setting.TMPDIR):
            os.popen(f"mkdir {setting.TMPDIR}")
        _pic_path = f"{setting.TMPDIR}/{int(time.time())}"

        if setting.IS_X11:
            pyscreenshot.grab().save(setting.SCREEN_CACHE)
            pyscreenshot.grab(bbox=(_x, _y, _x + width, _y + height)).save(
                _pic_path + ".png"
            )
            getattr(logger, log_level)(f"截取区域左上角 ({_x}, {_y}), 长宽 {width}, {height}")
        else:
            screen = os.popen(cls.wayland_screen_dbus).read().strip("\n")
            img = cv.imread(screen)
            cv.imwrite(_pic_path + ".png", img[_y: _y + height, _x: _x + width])
        return _pic_path

    @classmethod
    def find_image(
            cls,
            *widget,
            rate: Union[float, int] = None,
            multiple: bool = False,
            picture_abspath: str = None,
            screen_bbox: List[int] = None,
            log_level: str = "info",
            network_retry: int = None,
            pause: [int, float] = None,
            timeout: [int, float] = None,
            max_match_number: int = None,
    ):
        """
         在屏幕中区寻找小图，返回坐标，
         如果找不到，根据配置重试次数，每次间隔1秒
        :param picture_abspath:
        :param widget: 模板图片路径
        :param rate: 相似度
        :param multiple: 是否返回匹配到的多个目标
        :param screen_bbox: 截取屏幕上指定区域图片（仅支持X11下使用）；
            [x, y, w, h]
            x: 左上角横坐标；y: 左上角纵坐标；w: 宽度；h: 高度；根据匹配度返回坐标
        :param log_level: 日志级别
        :param network_retry: 连接服务器重试次数
        :param pause: 图像识别重试的间隔时间
        :param timeout: 最大匹配超时,单位秒
        :param max_match_number: 最大匹配次数
        :return: 坐标元组
        """
        network_retry = network_retry if network_retry else setting.NETWORK_RETRY
        pause = pause if pause else setting.PAUSE
        timeout = timeout if timeout else setting.TIMEOUT
        max_match_number = max_match_number if max_match_number else setting.MAX_MATCH_NUMBER

        retry_number = int(max_match_number)
        if retry_number < 0:
            raise ValueError("重试次数不能小于0")

        if rate is None:
            rate = float(setting.IMAGE_RATE)
        try:
            for element in widget:
                start_time = time.time()
                for _ in range(retry_number + 1):
                    locate = cls._match_image_by_opencv(
                        element,
                        rate,
                        multiple=multiple,
                        picture_abspath=picture_abspath,
                        screen_bbox=screen_bbox,
                        log_level=log_level,
                        network_retry=network_retry,
                    )
                    if not locate:
                        time.sleep(int(pause))
                    else:
                        return locate
                    end_time = time.time()
                    if end_time - start_time > timeout:
                        break
            raise TemplateElementNotFound(*widget)
        except Exception as exc:
            raise exc

    @staticmethod
    def find_image_color(widget):
        """
         获取图片的颜色值
        :param widget: 模板图片路径
        :return: 图片的颜色值
        """
        try:
            if not os.path.exists(widget):
                raise TemplatePictureNotExist(widget)
            _color = []
            with Image.open(widget) as image:
                pix = image.load()
                width = image.size[0]
                height = image.size[1]
                for _x in range(width):
                    for _y in range(height):
                        _r, _g, _b = pix[_x, _y]
                        _color.append((_r, _g, _b))
            return _color
        except Exception as exc:
            raise exc

    @classmethod
    def img_exists(cls, widget, rate=None):
        """
         判断图片是否存在，通常用于断言
        :param widget: 模块图片路径
        :param rate: 相似度
        :return:
        """
        if rate is None:
            rate = float(setting.IMAGE_RATE)
        try:
            return bool(cls.find_image(widget, rate=rate))
        # pylint: disable=broad-except
        except TemplateElementNotFound as exc:
            logger.warning(exc)
            return False

    @staticmethod
    def get_pic_px(pic_position):
        """
        获取图片的分辨率
        :param pic_position: 图片路径
        """
        return Image.open(os.path.expanduser(pic_position)).size

    @classmethod
    def get_during(
            cls,
            image_path: str,
            screen_time: Union[float, int],
            rate: float = None,
            pause: Union[int, float] = None,
            max_range: int = 10000,
    ):
        """
        在一段时间内截图多张图片进行识别，其中有一张图片识别成功即返回结果;
        适用于气泡类的断言，比如气泡在1秒内消失，如果用常规的图像识别则有可能无法识别到；
        :param image_path: 要识别的模板图片；
        :param screen_time: 截取屏幕图片的时间，单位秒；
        :param rate: 识别率；
        :param pause: 截取屏幕图片的间隔时间，默认不间隔；
        """
        during_path = "/tmp/youqu_during"
        os.system(f"rm -rf {during_path}")
        os.makedirs(during_path)
        pics = []
        start_time = time.time()
        for i in range(max_range):
            pic_name = f"{during_path}/{time.time()}_{i}.png"
            pics.append(pic_name)
            pyscreenshot.grab().save(pic_name)
            if time.time() - start_time >= screen_time:
                break
            if pause:
                time.sleep(pause)
        if not pics:
            raise ValueError
        for pic_path in pics:
            res = cls._match_image_by_opencv(
                image_path, rate=rate, picture_abspath=pic_path
            )
            if res:
                return res
        raise TemplateElementNotFound(image_path)


class ImageCenterByRGB:
    """
    By sliding and comparing the RGB values of small image and large image,
    locate the position of small image in large image.Some pre matching
    techniques are used to improve the speed.
    """

    @staticmethod
    def _check_match(_x, _y, small, bdata, sdata, rate):
        """
        Matching degree of small graph and large graph matching
        """
        same = 0
        diff = 0
        for i in range(small.width):
            for j in range(small.height):
                if bdata[_x + i, _y + j] == sdata[i, j]:
                    same = same + 1
                else:
                    diff = diff + 1
        similarity = same / (same + diff)
        return similarity >= rate

    @staticmethod
    def _pre_random_point(small):
        """
        Pre matching, take 10-20 points at random each time,
        and take coordinates randomly in the small graph
        """
        point_list = []
        count = random.randrange(10, 20)
        for _ in range(count):
            s_x = random.randrange(0, small.width)
            s_y = random.randrange(0, small.height)
            point_list.append([s_x, s_y])
        return point_list

    @staticmethod
    def _pre_random_match(_x, _y, point_list, bdata, sdata, rate):
        """
        In the small graph, several points are randomly
        selected for matching, and the matching degree is
        also set for the random points
        """
        same = 0
        diff = 0
        for point in point_list:
            if bdata[_x + point[0], _y + point[1]] == sdata[point[0], point[1]]:
                same = same + 1
            else:
                diff = diff + 1
        return same / (same + diff) >= rate

    @classmethod
    def image_center_by_rgb(cls, image_name=None, image_path=None, rate=setting.IMAGE_RATE):
        """
        By comparing the RGB values of the small image with the large
        image on the screen, the coordinates of the small image on
        the screen are returned.
        """
        if not image_path:
            image_path = setting.PIC_PATH
        small = Image.open(os.path.join(image_path, f"{image_name}.png"))
        sdata = small.load()
        big = pyscreenshot.grab()
        bdata = big.load()
        point_list = cls._pre_random_point(small)
        for _x in range(big.width - small.width):
            for _y in range(big.height - small.height):
                if cls._pre_random_match(_x, _y, point_list, bdata, sdata, rate):
                    if cls._check_match(_x, _y, small, bdata, sdata, rate):
                        return int(_x + small.width / 2), int(_y + small.height / 2)
        return False
