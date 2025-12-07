import requests
import re
import os
import time
import threading
import subprocess
import shutil
import json
from urllib.parse import urljoin, unquote, quote
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# 配置日志 - 使用demo2特定的日志文件名
logging.basicConfig(
    filename='demo2_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 断点续传相关常量 - 使用demo2特定的状态文件名
TASK_STATUS_FILE = 'demo2_status.json'
TASK_STATUSES = {
    'pending': '待处理',
    'downloading': '下载中',
    'merging': '合并中',
    'transcoding': '转码中',
    'completed': '已完成',
    'failed': '失败'
}

# 进度跟踪锁
lock = threading.Lock()

class ProgressBar:
    """进度条类"""
    def __init__(self, total):
        self.total = total
        self.completed = 0
        self.failed = 0
        
    def update(self, success=True):
        """更新进度"""
        with lock:
            if success:
                self.completed += 1
            else:
                self.failed += 1
            
            self._display()
    
    def _display(self):
        """显示进度条"""
        progress = self.completed + self.failed
        percent = (progress / self.total) * 100 if self.total > 0 else 0
        
        bar_length = 50
        filled_length = int(bar_length * progress // self.total)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        
        # 清除当前行并重新打印
        print(f'\r[{bar}] {percent:.1f}% | 已完成: {self.completed} | 失败: {self.failed} | 总计: {self.total}', end='', flush=True)
    
    def finish(self):
        """完成进度条显示"""
        print()

def get_m3u8_info(url):
    """获取m3u8文件信息并返回ts文件列表和基础URL"""
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.text
        print("获取到的m3u8内容:")
        print(data)
        
        # 提取ts文件名 - 改进正则表达式以匹配完整的TS文件名格式（包括路径和URL）
        ts_list = re.findall(r'([^\n\s"]+\.ts)', data)
        print("匹配到的ts文件名:")
        print(ts_list)
        
        if ts_list:
            # 获取基础URL
            base_url = url.rsplit('/', 1)[0] + '/'
            return ts_list, base_url
        else:
            print("没有匹配到任何ts文件")
            return [], ""
    except requests.exceptions.RequestException as e:
        print(f"获取m3u8信息错误: {e}")
        logging.error(f"获取m3u8信息错误: {e}")
        return [], ""

def download_ts_file_with_retry(ts_url, ts_path, max_retries=5):
    """下载单个ts文件，带重试机制"""
    retry_count = 0
    while retry_count < max_retries:
        try:
            resp = requests.get(ts_url, stream=True, timeout=10)
            resp.raise_for_status()
            
            # 获取文件大小
            total_size = int(resp.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(ts_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
            
            return True
        except requests.exceptions.RequestException as e:
            retry_count += 1
            print(f"\n下载失败 {ts_url}: {e}")
            logging.error(f"下载失败 {ts_url} (第{retry_count}次重试): {e}")
            
            if retry_count < max_retries:
                delay = min(2 ** retry_count, 10)  # 指数退避，最大延迟10秒
                print(f"{delay}秒后重试...")
                time.sleep(delay)
            else:
                print(f"已达到最大重试次数{max_retries}次，放弃下载")
                logging.error(f"已达到最大重试次数{max_retries}次，放弃下载 {ts_url}")
                return False

def merge_ts_files(ts_files, output_path):
    """合并ts文件"""
    try:
        with open(output_path, 'wb') as output_file:
            for ts_file in ts_files:
                if os.path.exists(ts_file):
                    with open(ts_file, 'rb') as f:
                        output_file.write(f.read())
                else:
                    print(f"\nTS文件不存在: {ts_file}")
                    logging.error(f"TS文件不存在: {ts_file}")
                    return False
        return True
    except Exception as e:
        print(f"\n合并ts文件错误: {e}")
        logging.error(f"合并ts文件错误: {e}")
        return False

def clean_ts_files(ts_files):
    """清理下载的ts文件"""
    for ts_file in ts_files:
        if os.path.exists(ts_file):
            os.remove(ts_file)


def extract_episode_info(url):
    """从URL中提取剧集信息"""
    # 解码URL中的中文
    decoded_url = unquote(url)
    print(f"解码后的URL: {decoded_url}")
    
    # 匹配剧集信息，如"第1集"、"第08集"等
    episode_pattern = r'第(\d{1,3})[集话]'
    match = re.search(episode_pattern, decoded_url)
    
    if match:
        episode_num = match.group(1)
        print(f"提取到剧集信息: 第{episode_num}集")
        return episode_num
    else:
        print("未找到剧集信息")
        return None


def save_task_status(task_status):
    """保存任务状态到JSON文件"""
    try:
        with open(TASK_STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(task_status, f, ensure_ascii=False, indent=2)
        logging.info(f"任务状态已保存到 {TASK_STATUS_FILE}")
    except Exception as e:
        print(f"保存任务状态失败: {e}")
        logging.error(f"保存任务状态失败: {e}")


def load_task_status():
    """从JSON文件加载任务状态"""
    try:
        if os.path.exists(TASK_STATUS_FILE):
            with open(TASK_STATUS_FILE, 'r', encoding='utf-8') as f:
                task_status = json.load(f)
            logging.info(f"从 {TASK_STATUS_FILE} 加载任务状态成功")
            return task_status
        else:
            return {}
    except Exception as e:
        print(f"加载任务状态失败: {e}")
        logging.error(f"加载任务状态失败: {e}")
        return {}


def update_task_status(episode_num, status, info=None):
    """更新单个任务的状态"""
    task_status = load_task_status()
    if episode_num not in task_status:
        task_status[episode_num] = {}
    task_status[episode_num]['status'] = status
    task_status[episode_num]['last_updated'] = time.strftime('%Y-%m-%d %H:%M:%S')
    if info:
        task_status[episode_num]['info'] = info
    save_task_status(task_status)


def get_pending_tasks():
    """获取所有待处理或未完成的任务"""
    task_status = load_task_status()
    pending_tasks = []
    
    for episode_num, status_info in task_status.items():
        if status_info.get('status') != 'completed':
            pending_tasks.append((int(episode_num), status_info))
    
    # 按集数排序
    pending_tasks.sort(key=lambda x: x[0])
    return pending_tasks

def transcode_video(input_path, output_path, target_format="mp4"):
    """视频转码函数，将视频转换为指定格式"""
    print(f"\n开始将视频从 {os.path.basename(input_path)} 转码为 {target_format} 格式...")
    logging.info(f"开始视频转码: {input_path} -> {output_path}")
    
    try:
        # 检查FFmpeg是否存在
        try:
            subprocess.run(['ffmpeg', '-version'], check=True, capture_output=True)
            use_ffmpeg = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("警告: 未找到FFmpeg，将使用文件复制方式模拟转码")
            use_ffmpeg = False
        
        if use_ffmpeg:
            # 使用FFmpeg进行实际转码
            command = [
                'ffmpeg', '-i', input_path,
                '-c:v', 'libx264', '-c:a', 'aac',
                '-strict', 'experimental',
                '-y',  # 覆盖现有文件
                output_path
            ]
            
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"视频转码成功: {output_path}")
                logging.info(f"视频转码成功: {output_path}")
                return True
            else:
                print(f"视频转码失败: {result.stderr}")
                logging.error(f"视频转码失败: {result.stderr}")
                return False
        else:
            # 模拟转码 - 直接复制文件
            shutil.copy2(input_path, output_path)
            print(f"视频复制完成（模拟转码）: {output_path}")
            logging.info(f"视频复制完成（模拟转码）: {output_path}")
            return True
            
    except Exception as e:
        print(f"视频转码过程中出错: {e}")
        logging.error(f"视频转码过程中出错: {e}")
        return False

def ensure_directories():
    """确保必要的目录存在"""
    temp_dir = os.path.join(os.getcwd(), 'data')  # 临时文件目录
    video_dir = os.path.join(os.getcwd(), 'video')  # 最终视频目录
    
    # 创建目录
    for dir_path in [temp_dir, video_dir]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"创建目录: {dir_path}")
    
    return temp_dir, video_dir


def process_single_episode(episode_num, m3u8_url, output_format="mp4", max_workers=8):
    """处理单个剧集的完整流程：爬取 -> 合成 -> 转码"""
    print(f"\n{'='*60}")
    print(f"开始处理第{episode_num}集")
    print(f"M3U8地址: {m3u8_url}")
    print(f"{'='*60}")
    
    # 确保目录结构
    temp_dir, video_dir = ensure_directories()
    
    # 准备文件名
    episode_str = str(episode_num).zfill(2)  # 补零为2位数，如01, 02
    temp_filename = f"第{episode_str}集.temp.mp4"  # 临时合成文件名
    final_filename = f"第{episode_str}集.{output_format}"  # 最终转码后的文件名
    
    # 检查是否已经完成
    final_output_path = os.path.join(video_dir, final_filename)
    if os.path.exists(final_output_path):
        print(f"第{episode_num}集已经处理完成，跳过")
        update_task_status(episode_num, 'completed', {'file_path': final_output_path, 'url': m3u8_url})
        return True
    
    # 更新任务状态为下载中
    update_task_status(episode_num, 'downloading', {'url': m3u8_url})
    
    try:
        # 获取m3u8信息
        ts_list, base_url = get_m3u8_info(m3u8_url)
        if not ts_list or not base_url:
            update_task_status(episode_num, 'failed', {'error': '无法获取m3u8信息', 'url': m3u8_url})
            return False
        
        # 准备下载任务
        download_tasks = []
        for ts_item in ts_list:
            # 提取文件名部分（去掉路径和URL前缀）用于本地存储
            ts_filename = ts_item.split('/')[-1]
            # 构建完整的TS URL（如果ts_item是完整URL，urljoin会保留它）
            ts_url = urljoin(base_url, ts_item)
            ts_path = os.path.join(temp_dir, ts_filename)
            download_tasks.append((ts_url, ts_path))
        
        # 下载所有ts文件（多线程）
        downloaded_ts_files = []
        total_ts = len(download_tasks)
        print(f"\n开始下载{total_ts}个ts文件...")
        
        # 创建进度条
        progress_bar = ProgressBar(total_ts)
        
        # 使用线程池下载
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有下载任务
            future_to_task = {executor.submit(download_ts_file_with_retry, ts_url, ts_path): (ts_url, ts_path) 
                             for ts_url, ts_path in download_tasks}
            
            # 处理下载结果
            for future in as_completed(future_to_task):
                ts_url, ts_path = future_to_task[future]
                try:
                    success = future.result()
                    if success:
                        downloaded_ts_files.append(ts_path)
                    progress_bar.update(success)
                except Exception as e:
                    print(f"\n处理下载任务时出错 {ts_url}: {e}")
                    logging.error(f"处理下载任务时出错 {ts_url}: {e}")
                    progress_bar.update(False)
        
        progress_bar.finish()
        
        if not downloaded_ts_files:
            print("没有成功下载任何ts文件")
            logging.error("没有成功下载任何ts文件")
            update_task_status(episode_num, 'failed', {'error': '没有成功下载任何ts文件', 'url': m3u8_url})
            return False
        
        # 更新任务状态为合并中
        update_task_status(episode_num, 'merging')
        
        # 合并ts文件（临时文件）
        temp_output_path = os.path.join(temp_dir, temp_filename)
        print(f"\n开始合并ts文件到临时文件: {temp_output_path}")
        
        if merge_ts_files(downloaded_ts_files, temp_output_path):
            print(f"视频合成成功: {temp_output_path}")
            logging.info(f"视频合成成功: {temp_output_path}")
            
            # 清理临时ts文件
            print("清理临时ts文件...")
            clean_ts_files(downloaded_ts_files)
            print("临时ts文件清理完成")
            
            # 更新任务状态为转码中
            update_task_status(episode_num, 'transcoding')
            
            # 转码视频到最终格式并保存到video目录
            if transcode_video(temp_output_path, final_output_path, output_format):
                # 清理临时合成文件
                if os.path.exists(temp_output_path):
                    os.remove(temp_output_path)
                    print(f"清理临时合成文件: {temp_output_path}")
                
                print(f"\n视频处理完成！最终文件保存到: {final_output_path}")
                update_task_status(episode_num, 'completed', {'file_path': final_output_path, 'url': m3u8_url})
                return True
            else:
                print("视频转码失败")
                logging.error("视频转码失败")
                update_task_status(episode_num, 'failed', {'error': '视频转码失败', 'url': m3u8_url})
                return False
        else:
            print("视频合成失败")
            logging.error("视频合成失败")
            update_task_status(episode_num, 'failed', {'error': '视频合成失败', 'url': m3u8_url})
            return False
            
    except Exception as e:
        print(f"处理第{episode_num}集时发生未知错误: {e}")
        logging.error(f"处理第{episode_num}集时发生未知错误: {e}")
        update_task_status(episode_num, 'failed', {'error': str(e), 'url': m3u8_url})
        return False

def read_m3u8_list(txt_path):
    """从指定的txt文件中读取m3u8地址列表"""
    m3u8_list = []
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                url = line.strip()
                if url:  # 跳过空行
                    # 验证URL是否为有效的m3u8地址
                    if url.endswith('.m3u8'):
                        m3u8_list.append(url)
                    else:
                        print(f"警告：第{i+1}行不是有效的m3u8地址: {url}")
                        logging.warning(f"第{i+1}行不是有效的m3u8地址: {url}")
        return m3u8_list
    except Exception as e:
        print(f"读取m3u8列表文件错误: {e}")
        logging.error(f"读取m3u8列表文件错误: {e}")
        return []

def show_task_summary():
    """显示任务完成情况摘要"""
    task_status = load_task_status()
    if not task_status:
        print("没有任务状态记录")
        return
    
    print("\n任务完成情况摘要:")
    status_counts = {}
    for episode_num, status_info in task_status.items():
        status = status_info.get('status', 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    for status, count in status_counts.items():
        print(f"{TASK_STATUSES.get(status, status)}: {count}集")

def main():
    """主程序入口"""
    # 询问用户txt文件路径
    txt_path = input("请输入存储m3u8地址的txt文件路径（默认text.txt）: ").strip()
    if not txt_path:
        txt_path = "text.txt"
    
    # 检查文件是否存在
    if not os.path.exists(txt_path):
        print(f"错误：文件 {txt_path} 不存在")
        logging.error(f"文件 {txt_path} 不存在")
        return
    
    # 读取m3u8地址列表
    m3u8_list = read_m3u8_list(txt_path)
    if not m3u8_list:
        print("没有找到有效的m3u8地址")
        logging.error("没有找到有效的m3u8地址")
        return
    
    print(f"\n成功读取到 {len(m3u8_list)} 个有效的m3u8地址")
    
    # 加载任务状态
    task_status = load_task_status()
    pending_tasks = get_pending_tasks()
    
    # 询问用户是否继续未完成的任务
    if pending_tasks:
        print("\n发现未完成的任务:")
        for episode_num, status_info in pending_tasks:
            status = status_info.get('status', 'unknown')
            print(f"第{episode_num}集: {TASK_STATUSES.get(status, status)}")
        
        continue_task = input("是否继续未完成的任务？(y/n): ").lower()
        if continue_task == 'y':
            # 继续未完成的任务
            print(f"\n将继续处理未完成的任务")
        else:
            # 重新开始，处理所有集数
            print(f"\n将重新处理所有集数")
            pending_tasks = []  # 清空未完成任务列表，重新处理所有
    
    start_total_time = time.time()
    
    # 处理每一集（顺序执行，确保完成一个再开始下一个）
    for i, m3u8_url in enumerate(m3u8_list):
        episode_num = i + 1  # 集数从1开始
        
        # 检查是否需要跳过（如果继续未完成任务且当前任务已完成）
        if pending_tasks and episode_num not in [ep_num for ep_num, _ in pending_tasks]:
            print(f"\n第{episode_num}集已经处理完成，跳过")
            continue
        
        # 处理当前集数
        print(f"\n--- 开始处理第{episode_num}集 ---")
        try:
            if process_single_episode(episode_num, m3u8_url, output_format="mp4", max_workers=8):
                print(f"\n第{episode_num}集处理完成！")
            else:
                print(f"\n第{episode_num}集处理失败！")
        except Exception as e:
            print(f"\n处理第{episode_num}集时发生错误: {e}")
            logging.error(f"处理第{episode_num}集时发生错误: {e}")
        
        # 每集之间休息1-2秒，避免请求过于频繁
        time.sleep(1 + time.time() % 1)
    
    end_total_time = time.time()
    print(f"\n{'='*60}")
    print(f"所有指定集数处理完成！总耗时: {end_total_time - start_total_time:.2f}秒")
    
    # 显示任务完成情况
    show_task_summary()

if __name__ == "__main__":
    main()