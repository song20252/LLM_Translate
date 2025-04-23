1、本项目基于auto_ai_subtitle改写，链接如下：
https://github.com/qinL-cdy/auto_ai_subtitle


2、功能：
audio_process
get_audio.py 批量提取录音文件
whisper_tools
whisper_tool.py 语音文件转写成文本
muti_main.py 多gpu并行处理whisper_tool任务
translate
OpenAITranslator.py 封装了openai接口的大模型翻译
main.py 执行翻译任务


3、依赖:
whisper
ffmpeg
torch


