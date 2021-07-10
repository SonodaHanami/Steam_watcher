# Steam_watcher
这是 [prcbot/yobot](https://github.com/pcrbot/yobot) 的自定义插件

## 使用方法

首先 [部署一个可以正常运行的 **yobot 源码版**](https://yobot.win/install/mirai/) ，部署完之后：

```sh
# 在 ybplugins 目录下克隆本项目
cd yobot/src/client/ybplugins
git clone https://github.com/SonodaHanami/Steam_watcher

# 安装依赖
cd Steam_watcher
pip3 install -r requirements.txt --user
# 国内可加上参数 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

然后将 Steam_watcher 导入 yobot ，请看[这个例子](https://github.com/SonodaHanami/yobot/commit/a64af42dd43cd25ad04b4aabc91d06ad95a16aba)

启动 yobot ，第一次启动 Steam_watcher 后会在 Steam_watcher 文件夹下自动生成 config.json，修改它
```json
{
    "ADMIN": "123456789",   // 填写管理员的QQ号
    "BOT": "987654321",     // 填写BOT的QQ号
    "STEAM_APIKEY": ""      // 填写Steam的APIKEY
}
```

然后重新启动yobot

## 功能表
下次一定写
