# Steam_watcher
这是 [prcbot/yobot](https://github.com/pcrbot/yobot) 的自定义插件，用于Steam相关内容的自动播报和手动查询

## 功能表
下次一定写


## 使用方法

### 事前准备

[获取 Steam APIKEY](https://steamcommunity.com/dev/apikey)

### Linux

#### 0. yobot 源码版

本插件基于 yobot 运行，所以首先需要 [部署一个可以正常运行的 **yobot 源码版**](https://yobot.win/install/Linux-gocqhttp/)

#### 1. 下载本项目

```sh
# 在 ybplugins 目录下克隆本项目
cd yobot/src/client/ybplugins
git clone https://github.com/SonodaHanami/Steam_watcher
```

#### 2. 安装依赖
```
cd Steam_watcher
pip3 install -r requirements.txt --user
# 国内可加上参数 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 3. 导入

将 Steam_watcher 导入 yobot ，请参考 [这个例子](https://github.com/SonodaHanami/yobot/commit/80b5857ca722cf6221b40b369ac3375059b8b0b6) 修改 yobot.py

#### 4. 填写配置文件

启动 yobot ，第一次启动 Steam_watcher 后会在 Steam_watcher 文件夹下自动生成 config.json，修改它
```json
{
    "ADMIN": "123456789",   // 填写管理员的QQ号
    "BOT": "987654321",     // 填写BOT的QQ号
    "STEAM_APIKEY": ""      // 填写 Steam APIKEY
}
```

#### 5. 应该可以了

重新启动yobot，开始使用

### Windows

#### 0. yobot 源码版

本插件基于 yobot 运行，所以首先需要 [部署一个可以正常运行的 **yobot 源码版**](https://yobot.win/install/Windows-yobot/)

#### 1. 下载本项目

推荐使用 [Github Desktop](https://desktop.github.com/) 在 ybplugins 目录下克隆本项目，后续更新可直接pull

<details>
  <summary>下载源码（不推荐）</summary>
  下载 https://github.com/SonodaHanami/Steam_watcher/archive/refs/heads/master.zip ，将整个 Steam_watcher 文件夹解压到 ybplugins 目录下
</details>

#### 2. 安装依赖
进入 Steam_watcher 文件夹，在空白处Shift+右键，点击“在此处打开 PowerShell 窗口”
```PowerShell
pip3 install -r requirements.txt --user
# 国内可加上参数 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 3. 导入

将 Steam_watcher 导入 yobot ，请参考 [这个例子](https://github.com/SonodaHanami/yobot/commit/80b5857ca722cf6221b40b369ac3375059b8b0b6) 修改 yobot.py

#### 4. 填写配置文件

启动 yobot ，第一次启动 Steam_watcher 后会在 Steam_watcher 文件夹下自动生成 config.json，修改它
```json
{
    "ADMIN": "123456789",   // 填写管理员的QQ号
    "BOT": "987654321",     // 填写BOT的QQ号
    "STEAM_APIKEY": ""      // 填写 Steam APIKEY
}
```

#### 5. 应该可以了

重新启动yobot，开始使用
