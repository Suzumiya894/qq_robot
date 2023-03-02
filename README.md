# qq_robot
基于go-cqhttp的qq群聊机器人

感谢[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)和[chatGPT逆向工程](https://github.com/acheong08/ChatGPT)的开发者

## 版本更新

- 3.0版本，将函数封装为对象，全部函数改为异步实现，增加chatGPT接口
- 2.0版本，增加复读次数过多，会将指定照片设置为群头像的新功能
- 1.0版本，检测复读行为，次数达到一定数量（每个人有不同的信用值）后禁言对方，并降低他的信用值
