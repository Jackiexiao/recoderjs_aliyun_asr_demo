# recoderjs_aliyun_asr_demo
[recoderjs](https://github.com/xiangyuecn/Recorder) + 阿里云ASR 实时语音识别接口代码演示

[原始仓库中关于实时语音识别的代码](https://github.com/xiangyuecn/Recorder/blob/master/index.html)写的不太简洁，不便于新手学习，所以重新简化了一下，只保留语音识别相关的逻辑

## 使用方法
1. 用编辑器打开 `NodeJsServer_asr.aliyun.short.js` 文件，文件开头有 `【必填】` 项，根据注释完成配置：`AccessKey`、`Secret`、`Appkey`，可提供多个Appkey对应不同的语言模型。
2. 直接命令行执行 `node NodeJsServer_asr.aliyun.short.js` 运行服务，**注意：需要先在js文件内配置密钥**。
3. 本地电脑打开 `index.html` 文件，点击录音按钮开始录音，结束录音后会自动识别语音并显示结果。

详情参考：
https://github.com/xiangyuecn/Recorder/blob/master/assets/demo-asr/README.md


这里只修改了 `index.html` 文件，其他文件都是 `recoderjs` 库的，只复制了必要的文件。