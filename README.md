# MCDRServerRunner
一个适用于MCDReforged的Java服务端套壳，支持通过控制台命令伪造服务端日志内容方便进行测试。

## 食用方法
默认情况下，从源码或者release下载run_server.py，放到MCDR根目录中，接着在run_server.py中修改用于启动服务端的命令，然后修改MCDR配置中的启动命令，将其改为python run_server.py即可。
你可以使用`fakelog <消息内容>`来伪造一个来自服务端的消息，除此之外，服务端应该会照常运行。

## 配置
脚本没有设置任何外部配置，有需要的地方请自行修改源码。（用于伪造服务端日志的命令也可以在源码里面改）

## 免责声明
不保证后续更新。
