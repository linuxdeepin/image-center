# image-center
图像识别定位某个元素在当前屏幕中的坐标；

在自动化测试中获取到元素坐标之后，可以传入到键鼠工具，从而实现对目标元素的操作。

---

**Documentation**: <a href="https://linuxdeepin.github.io/image-center" target="_blank">https://linuxdeepin.github.io/image-center</a>

**Source Code**: <a href="https://github.com/linuxdeepin/image-center" target="_blank">https://github.com/linuxdeepin/image-center</a>

---

## 安装

```console
pip install image-center
```

如果想在本机直接使用图像识别，还需要在本机安装OpenCV

```shell
sudo apt install python3-opencv
```

## 使用说明

截取目标元素图片，将图片保存到某个路径；

```python
from image_center import ImageCenter

ImageCenter.find_image("~/Desktop/test.png")
```

返回 `test.png` 在当前屏幕中的位置。

## RPC服务

如果不想在本机安装OpenCV，或者你的机器无法安装OpenCV，可以在服务端安装OpenCV（安装方法和上面一样）；

服务端启动方法：

```python
from image_center.server import server
from image_center.conf import setting

setting.PORT = 8889  # 默认端口是8889，可以修改为其他端口；

server()
```

执行这个代码就可以启动服务了；

客户端使用方法和前面一样，唯一需要配置的是服务端的IP和端口。

```python
from image_center import ImageCenter
from image_center.conf import setting

setting.SERCER_IP = "192.168.2.1"  # 服务端IP
setting.PORT = 8889 # 和服务端端口保持一致

ImageCenter.find_image("~/Desktop/test.png") # test.png是你自己截的图，路径也修改成你自己的路径
```