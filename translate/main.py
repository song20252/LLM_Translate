import re
import os
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from OpenAITranslator import OpenAITranslator
import yaml

def should_translate(line: str) -> bool:
    """判断行是否需要翻译"""
    line = line.strip()
    return bool(
        line 
        and not line.isdigit() 
        and not re.match(r"^\d{2}:\d{2}:\d{2},\d{3}\s-->\s\d{2}:\d{2}:\d{2},\d{3}$", line)
        and not re.fullmatch(r"[\s\.,!?;:\"'-]+", line)
    )

def read_file_lines(file_path: str) -> List[str]:
    """读取文件并返回行列表"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.rstrip('\n') for line in f]

def get_pending_lines(lines: List[str]) -> List[Tuple[int, str]]:
    """获取待翻译的行号和内容"""
    pending_lines = []
    for idx, line in enumerate(lines):
        if(should_translate(line)):
            pending_lines.append((idx, line))
    return pending_lines

def split_into_chunks(pending_lines: List[Tuple[int, str]], chunk_size: int) -> List[List[Tuple[int, str]]]:
    """将待翻译的行按指定大小切块"""
    return [pending_lines[i:i + chunk_size] for i in range(0, len(pending_lines), chunk_size)]
                
def translate_chunk(chunk: List[Tuple[int, str]], translator: OpenAITranslator, prompt: str) -> Dict[int, str]:
    """
    对一个块中的所有行进行翻译。
    :param chunk: 包含 (行号, 内容) 的列表。
    :return: 翻译结果字典 {行号: 翻译后的文本}
    """
    translator.translate_batch
    translations = {}
    # 提取字符串部分
    texts = [text for _, text in chunk]
    translated_texts = translator.translate_batch(prompt, texts)
    translations = {idx: translated_text for (idx, _), translated_text in zip(chunk, translated_texts)}
    return translations
    
    
def do_translate(input_file: str, output_file: str, prompt: str, api_key: str, base_url: str, max_workers: int, chunk_size: int) -> None:
    translator = OpenAITranslator(api_key, base_url)
    # 读取文件内容
    lines = read_file_lines(input_file)
    # 获取待翻译的行
    pending_lines = get_pending_lines(lines)
    # 分割成块
    chunks = split_into_chunks(pending_lines, chunk_size)
    all_translations = {} 
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(partial(translate_chunk, translator=translator, prompt=prompt), chunk): chunk
            for chunk in chunks
        }
        
        for future in as_completed(futures):
            translations = future.result()
            all_translations.update(translations)
            print(f"Processed chunk with {len(translations)} translations.")
            
    # 构建最终结果，保持原始顺序
    final_lines = []
    for idx, original_line in enumerate(lines):
        if idx in all_translations:
            final_lines.append(all_translations[idx])
        else:
            final_lines.append(original_line)
            
    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(final_lines))


def process_directory(input_dir: str, output_dir: str, prompt: str, api_key: str, base_url: str, max_workers: int, chunk_size: int) -> None:
    """
    遍历 input_dir 目录下的所有 .srt 文件，逐个翻译并保存到 output_dir。
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 遍历输入目录中的所有 .srt 文件
    for file_name in os.listdir(input_dir):
        if file_name.endswith(".srt"):
            input_file = os.path.join(input_dir, file_name)
            output_file = os.path.join(output_dir, file_name.replace(".srt", "_cn.srt"))
            
             # 检查输出文件是否已存在
            if os.path.exists(output_file):
                print(f"Translated file already exists, skipping: {output_file}")
                continue
                
            print(f"Processing file: {input_file}")
            do_translate(input_file, output_file, prompt, api_key, base_url, max_workers, chunk_size)
            print(f"Translated file saved to: {output_file}")
        
if __name__ == '__main__':
    
    with open('config.yaml', encoding='utf-8') as f:
        config = yaml.load(f.read(), Loader=yaml.FullLoader)
   
    input_dir = config['input_dir']
    output_dir = config['output_dir']
    chunk_size = config['chunk_size']
    max_workers = config['max_workers']
    api_key = config['api_key']
    base_url = config['base_url']
    prompt = config['prompt']
    
    # 处理目录中的所有 .srt 文件
    process_directory(input_dir, output_dir, prompt, api_key, base_url, max_workers, chunk_size)
