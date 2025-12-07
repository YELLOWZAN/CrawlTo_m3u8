# 视频爬取工具 README

## 项目概述

这是一个功能强大的视频爬取工具，用于从m3u8地址下载视频片段（TS文件），合并并转码为MP4格式。工具支持断点续传、多线程下载、进度跟踪和日志记录等功能，能够高效可靠地处理视频下载任务。

## 环境需求

### 开发环境
- Python 3.6+：确保安装了Python 3.6或更高版本
- 开发工具：推荐使用PyCharm、VS Code等Python开发环境

### 运行环境
- Windows/macOS/Linux：跨平台支持
- 网络连接：需要稳定的网络连接用于下载视频片段

### 依赖组件
- requests：用于发送HTTP请求下载视频片段
- 可选依赖：
  - FFmpeg：用于实际视频转码（如果不安装，将使用文件复制方式模拟转码）

## 安装和启动步骤

### 1. 安装Python（如果未安装）
- 从[Python官方网站](https://www.python.org/downloads/)下载并安装Python 3.7或更高版本
- 确保在安装过程中勾选"Add Python to PATH"

### 2. 安装依赖

```bash
pip install requests
```

### 3. 安装FFmpeg（可选）

#### Windows安装步骤：
1. 从[FFmpeg官网](https://ffmpeg.org/download.html)下载Windows版本的FFmpeg
2. 解压下载的文件到合适的位置（例如：`D:\ffmpeg`）
3. 将FFmpeg的bin目录添加到系统环境变量Path中（例如：`D:\ffmpeg\bin`）
4. 验证安装：在命令行中输入`ffmpeg -version`，如果显示版本信息则安装成功

#### macOS安装步骤：
```bash
brew install ffmpeg
```

#### Linux安装步骤：
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

### 4. 启动开发环境

```bash
# 克隆或下载项目文件到本地目录
cd /path/to/project

# 运行demo.py
python demo.py

# 或运行demo2.py
python demo2.py
```

## 使用方式

### demo.py 使用指南

1. **启动程序**：
   ```bash
   python demo.py
   ```

2. **输入示例URL**：
   程序会提示输入示例m3u8 URL，例如：
   ```
   https://example.com/video/episode1.m3u8
   ```

3. **选择是否继续未完成任务**：
   如果之前有未完成的任务，程序会询问是否继续处理

4. **输入集数范围**：
   - 输入单个集数：`1`
   - 输入集数范围：`1-10`
   - 按Enter键处理所有集数

5. **等待处理完成**：
   程序会自动下载、合并和转码视频，完成后会显示任务摘要

### demo2.py 使用指南

1. **准备m3u8地址列表文件**：
   创建一个txt文件（例如：`url.txt`），每行一个m3u8地址：
   ```
   https://example.com/video/episode1.m3u8
   https://example.com/video/episode2.m3u8
   https://example.com/video/episode3.m3u8
   ```

2. **启动程序**：
   ```bash
   python demo2.py
   ```

3. **输入txt文件路径**：
   程序会提示输入m3u8地址列表文件路径，默认使用`text.txt`

4. **选择是否继续未完成任务**：
   如果之前有未完成的任务，程序会询问是否继续处理

5. **等待处理完成**：
   程序会自动处理txt文件中的所有m3u8地址，完成后会显示任务摘要

## 关键配置项

### demo.py 配置项

| 配置项 | 描述 | 默认值 | 位置 |
|--------|------|--------|------|
| `TASK_STATUS_FILE` | 任务状态文件路径 | `task_status.json` | 第20行 |
| `download.log` | 日志文件路径 | `download.log` | 第15行 |
| `max_retries` | 下载重试次数 | `5` | `download_ts_file_with_retry`函数 |
| `max_workers` | 最大下载线程数 | `8` | `process_single_episode`函数 |
| `target_format` | 目标视频格式 | `mp4` | `transcode_video`函数 |

### demo2.py 配置项

| 配置项 | 描述 | 默认值 | 位置 |
|--------|------|--------|------|
| `TASK_STATUS_FILE` | 任务状态文件路径 | `demo2_status.json` | 第21行 |
| `demo2_log.txt` | 日志文件路径 | `demo2_log.txt` | 第15行 |
| `default_txt_path` | 默认m3u8列表文件 | `text.txt` | `main`函数 |
| `max_retries` | 下载重试次数 | `5` | `download_ts_file_with_retry`函数 |
| `max_workers` | 最大下载线程数 | `8` | `process_single_episode`函数 |
| `target_format` | 目标视频格式 | `mp4` | `transcode_video`函数 |

## 项目结构

```
scrwl/
├── demo.py                # 原始视频爬取工具
├── demo2.py               # 增强版视频爬取工具（支持批量处理）
├── download.log           # demo.py 日志文件
├── demo2_log.txt          # demo2.py 日志文件
├── task_status.json       # demo.py 任务状态文件
├── demo2_status.json      # demo2.py 任务状态文件
├── data/                  # 存储下载的TS文件目录
├── video/                 # 存储最终转码后的视频文件目录
└── README.md              # 项目说明文档
```

### 主要功能模块

1. **视频片段下载**：
   - `download_ts_file_with_retry`：下载单个TS文件，带重试机制
   - 多线程下载支持，提高下载效率

2. **视频处理**：
   - `merge_ts_files`：合并多个TS文件为单个视频文件
   - `transcode_video`：将视频转码为指定格式（支持FFmpeg和文件复制两种方式）

3. **任务管理**：
   - `save_task_status`：保存任务状态到JSON文件
   - `load_task_status`：从JSON文件加载任务状态
   - `update_task_status`：更新任务状态
   - `get_pending_tasks`：获取未完成的任务

4. **进度跟踪**：
   - `ProgressBar`类：显示下载进度条
   - 实时更新已完成/失败的TS文件数量

## 常见问题解决方法

### 1. 下载TS文件时出现404错误

**问题**：下载TS文件时出现"404 Not Found"错误

**解决方法**：
- 检查m3u8地址是否正确
- 检查TS文件名格式是否与实际服务器上的文件名匹配
- 可能是服务器端的TS文件路径发生了变化

### 2. 视频合并失败

**问题**：TS文件下载完成，但合并失败

**解决方法**：
- 确保所有TS文件都成功下载
- 检查文件权限，确保程序有写入权限
- 检查磁盘空间是否足够

### 3. 转码失败

**问题**：视频合并成功，但转码失败

**解决方法**：
- 确保已正确安装FFmpeg并添加到环境变量
- 如果不需要实际转码，可以使用文件复制方式（程序会自动降级）

### 4. 程序运行缓慢

**问题**：下载和处理视频的速度很慢

**解决方法**：
- 检查网络连接是否稳定
- 减少并行下载线程数（修改`max_workers`参数）
- 确保计算机性能足够处理视频转码任务

### 5. 断点续传功能失效

**问题**：程序重启后无法继续之前的任务

**解决方法**：
- 确保`task_status.json`或`demo2_status.json`文件存在且未被损坏
- 检查任务状态文件的格式是否正确

## demo2 与 demo 的对比分析

### 功能新增

1. **批量处理支持**：
   - demo2支持从txt文件读取多个m3u8地址，实现批量处理
   - 每行一个m3u8地址，自动忽略空行和无效地址

2. **文件名标准化**：
   - demo2将视频文件命名为"第X集.mp4"格式，更加直观
   - 自动为集数补零（如"第01集.mp4"），确保文件排序正确

3. **增强的TS文件解析**：
   - demo2使用更强大的正则表达式解析m3u8文件
   - 支持更复杂的TS文件名格式，包括路径和URL前缀

### 代码重构

1. **函数参数简化**：
   - `process_single_episode`函数直接接受m3u8_url作为参数，无需构建URL模式
   - 简化了函数调用流程，提高了代码可读性

2. **目录结构优化**：
   - 统一使用`temp_dir`和`video_dir`变量管理临时文件和输出文件目录
   - 提高了代码的可维护性

3. **TS文件处理改进**：
   - 改进了TS文件名提取逻辑，支持从完整URL中提取文件名
   - 增强了URL构建逻辑，确保正确拼接TS文件的完整URL

### 性能优化

1. **下载任务管理**：
   - 优化了下载任务的准备和执行流程
   - 提高了多线程下载的效率

2. **内存使用优化**：
   - 改进了文件处理逻辑，减少了内存占用
   - 更高效地处理大量TS文件

### 问题修复

1. **TS文件名解析问题**：
   - 修复了demo中无法处理非数字命名的TS文件的问题
   - 支持包含字母和特殊字符的TS文件名

2. **URL构建问题**：
   - 修复了demo中URL模式构建可能导致的错误
   - demo2直接使用完整的m3u8_url，避免了URL模式构建的复杂性

### demo2 使用指南

#### 1. 创建m3u8地址列表文件

创建一个txt文件（例如：`url.txt`），每行一个m3u8地址：

```
https://vip1.lz-cdn5.com/20220518/18545_3aa2caac/1200k/hls/mixed.m3u8
https://vip1.lz-cdn5.com/20220518/18552_f2919fd3/1200k/hls/mixed.m3u8
https://example.com/video/episode3.m3u8
```

#### 2. 运行demo2.py

```bash
python demo2.py
```

#### 3. 输入文件路径

程序会提示输入m3u8地址列表文件路径：

```
请输入存储m3u8地址的txt文件路径（默认text.txt）: url.txt
```

#### 4. 选择是否继续未完成任务

如果之前有未完成的任务，程序会询问是否继续处理：

```
发现未完成的任务:
第1集: 下载中
第2集: 失败
是否继续未完成的任务？(y/n): y
```

#### 5. 等待处理完成

程序会自动处理所有m3u8地址，完成后显示任务摘要：

```
所有指定集数处理完成！总耗时: 123.45秒

任务完成情况摘要:
已完成: 2集
失败: 1集
```

#### 注意事项

1. **文件格式要求**：
   - txt文件中的每个m3u8地址必须以`.m3u8`结尾
   - 空行会被自动忽略
   - 无效的地址会被记录在日志中并跳过

2. **任务状态管理**：
   - demo2使用`demo2_status.json`单独存储任务状态，与demo的`task_status.json`互不影响
   - 日志文件使用`demo2_log.txt`，方便区分不同版本的运行记录

3. **视频文件命名**：
   - 视频文件将命名为"第X集.mp4"格式
   - 集数从1开始，自动递增
   - 集数不足2位时会自动补零（如"第01集.mp4"）

4. **错误处理**：
   - 单个m3u8地址处理失败不会影响其他地址的处理
   - 失败的任务会被记录在任务状态文件中，可以选择重新处理

## 总结

本工具提供了高效可靠的视频爬取功能，支持断点续传、多线程下载和进度跟踪等特性。demo2版本在demo的基础上增加了批量处理支持，改进了TS文件解析逻辑，提供了更友好的用户体验。无论是单个视频还是批量视频下载任务，本工具都能满足您的需求。

如果您在使用过程中遇到问题，欢迎查阅本文档的常见问题解决方法，或查看日志文件获取详细信息。