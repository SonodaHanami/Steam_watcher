# Steam_watcher
这是 [prcbot/yobot](https://github.com/pcrbot/yobot) 的自定义插件，可自动播报玩家的Steam游戏状态和DOTA2图文战报

## 都有些什么功能？

本插件可以在用户绑定后自动推送Steam游戏状态的更新和 **Dota2** 图文战报，以及提供一些手动查询功能

## 指令列表

`atbot` 表示需要@BOT

`atsb` 表示@某人

`xxx` `yyy` 等表示自定义参数

`[]` 方括号表示参数可以省略

### Steam

负责Steam相关的功能

| 指令 | 说明 |
| :----- | :---- |
| Steam帮助 | 查看帮助 |
| 订阅Steam | 在本群开启Steam内容的推送 |
| 取消订阅Steam| 在本群关闭Steam内容的推送 |
| 绑定Steam `好友代码` | 绑定Steam账号，一人一号<br>可直接覆盖绑定|
| 解除绑定Steam | 解除绑定Steam账号 |
| `xxx`在干嘛 | 查询`xxx`的Steam游戏状态 |
| 查询`xxx`的天梯段位 | |
| 查询`xxx`的常用英雄 | |
| 查询`xxx`的英雄池 | |

### Whois

负责区分各个群的各位群友

| 指令<sup>0</sup> | 说明 |
| :----- | :---- |
| `atbot` 我是`xxx` | 为自己增加一个别名`xxx`<sup>1</sup> |
| `atbot` 请叫我`xxx` | 为自己增加一个别名`xxx`并设为默认<sup>2</sup> |
| `atbot` 我不是`xxx` | 删除自己的别名`xxx` |
| `atbot` `yyy`是`xxx` | 为`yyy`增加一个别名`xxx`<sup>3</sup> |
| `xxx`是谁？ | 查询`xxx`的别名 |
| `xxx`是不是`yyy`？ | 比对`xxx`和`yyy`的默认别名 |
| 查询群友 | 查询群内所有拥有别名的群友的默认别名 |

<sup>0</sup> 简单地说，涉及**修改**的指令需要 `atbot`，而**查询**的指令不需要

<sup>1, 2</sup> 一个人可以拥有多个别名，其中第一个是默认别名

<sup>3</sup> `yyy`可以是`atsb`

## 使用方法

### 事前准备

#### Steam APIKEY

[获取 Steam APIKEY](https://steamcommunity.com/dev/apikey)

Steam APIKEY 的权限与其所属账号挂钩，要看到被观察者的游戏状态，需要满足以下两个条件之一

- 被观察者的 Steam 隐私设置中游戏详情设置为 **公开** ，且好友与聊天状态设置为在线
- APIKEY 账号与被观察者为好友，被观察者的 Steam 隐私设置中游戏详情设置为 **仅限好友** ，且好友与聊天状态设置为在线

条件不满足时，从 API 获取到的被观察者的游戏状态为空，即没在玩游戏

### Linux

#### 0. yobot 源码版

本插件基于 yobot 运行，所以首先需要 [部署 **yobot 源码版** 和 **go-cqhttp**](https://yobot.win/install/Linux-gocqhttp/)，并保持两者同时运行

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

将 Steam_watcher 导入 yobot ，请参考 [这个例子](https://github.com/SonodaHanami/yobot/commit/80b5857ca722cf6221b40b369ac3375059b8b0b6) 修改 `yobot.py`

#### 4. 填写配置文件

启动 yobot ，第一次启动 Steam_watcher 后会在 `Steam_watcher` 文件夹下自动生成 `config.json`，修改它
```json
{
    "ADMIN": "123456789",   // 填写管理员的QQ号
    "BOT": "987654321",     // 填写BOT的QQ号
    "STEAM_APIKEY": ""      // 填写 Steam APIKEY
}
```

#### 5. 应该可以了

重新启动 yobot ，开始使用

### Windows

#### 0. yobot 源码版

本插件基于 yobot 运行，所以首先需要 [部署 **yobot 源码版** 和 **go-cqhttp**](https://yobot.win/install/Windows-yobot/)，并保持两者同时运行

#### 1. 下载本项目

推荐使用 [Github Desktop](https://desktop.github.com/) 在 `yobot/src/client/ybplugins` 目录下克隆本项目，后续更新可直接pull

<details>
  <summary>下载源码（不推荐）</summary>
  下载 https://github.com/SonodaHanami/Steam_watcher/archive/refs/heads/master.zip ，将整个 Steam_watcher 文件夹解压到 yobot/src/client/ybplugins 目录下
</details>

完成本步骤后，项目目录结构应该如下所示（仅列出本文档相关的关键文件/文件夹示意）
```
yobot
  └─src
      └─client
          ├─yobot.py
          └─ybplugins
              └─Steam_watcher
                  └─steam.py
```
#### 2. 安装依赖
进入 `Steam_watcher` 文件夹，在空白处Shift+右键，点击“在此处打开 PowerShell 窗口”（或者命令提示符）
```PowerShell
pip3 install -r requirements.txt --user
# 国内可加上参数 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 3. 导入

将 Steam_watcher 导入 yobot ，请参考 [这个例子](https://github.com/SonodaHanami/yobot/commit/80b5857ca722cf6221b40b369ac3375059b8b0b6) 修改 `yobot.py`

#### 4. 填写配置文件

启动 yobot ，第一次启动 Steam_watcher 后会在 `Steam_watcher` 文件夹下自动生成 `config.json`，修改它
```json
{
    "ADMIN": "123456789",   // 填写管理员的QQ号
    "BOT": "987654321",     // 填写BOT的QQ号
    "STEAM_APIKEY": ""      // 填写 Steam APIKEY
}
```

#### 5. 应该可以了

重新启动 yobot ，开始使用

### 开始使用

#### 1. 订阅Steam

在群内发送“订阅Steam”，开启Steam内容的推送

#### 2. 成为群友

在群内发送“`atbot` 我是`xxx`”，为自己添加一个别名

<details>
  <summary>为什么需要这样做？</summary>
    这样做的目的是隔离。因为bot可以加入多个群，同一个人也可以同时在不同的的群里，但是同一个人的推送不一定要发到所有群<br>
    bot仅向每个群里发送<b>绑定了Steam的群友</b>的推送。<br>
    举个例子：<br>
    有A和B两个群，两个群里都有枫哥、甲哥、翔哥和bot，枫哥、甲哥和翔哥各自都绑定了Steam<br>
    A群的群友有枫哥和甲哥<br>
    B群的群友有枫哥和翔哥<br>
    则bot会向A群发送枫哥和甲哥的推送，向B群发送枫哥和翔哥的推送<br>
    或者说，枫哥的推送会被bot发送到A和B两个群，甲哥的推送只会被bot发送到A群，翔哥的推送只会被bot发送到B群
</details>

#### 3. 绑定Steam

在群内发送“绑定Steam `好友代码`”，绑定自己的Steam号

#### 4. 试一下

在群内发送“`xxx`是谁？”，bot将回复`xxx`的别名

在群内发送“查询群友”，bot将回复该群的群友列表

在群内发送“`xxx`在干嘛”，bot将回复`xxx`的Steam游戏状态