# -*- coding: utf-8 -*-
import os
import re
import uuid
import shutil
import time
from PIL import Image

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}

class ImageProcessor:
    def __init__(self, output_callback, progress_callback=None, status_callback=None, stop_flag=None):
        self.output = output_callback
        self.progress = progress_callback
        self.status = status_callback
        self.skip_all = False
        self.processed_count = 0
        self.stop_flag = stop_flag

    def is_image_file(self, filename):
        return os.path.splitext(filename)[1].lower() in IMAGE_EXTENSIONS

    def delete_small_images(self, folder, size_limit_kb=200):
        size_limit_bytes = size_limit_kb * 1024
        deleted = 0
        files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f)) and self.is_image_file(f)]
        for idx, fname in enumerate(files):
            if self.stop_flag and self.stop_flag.is_set():
                self.output("用户停止，删除小图中断", 'error')
                break
            fpath = os.path.join(folder, fname)
            try:
                if not os.path.exists(fpath):
                    continue
                if os.path.getsize(fpath) < size_limit_bytes:
                    os.remove(fpath)
                    self.output(f"已删除: {fname}", 'info')
                    deleted += 1
            except:
                pass
            if self.progress:
                self.progress((idx+1)/len(files) * 30)
        return deleted

    def collect_remaining_images(self, folder):
        return sorted([f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f)) and self.is_image_file(f)], key=lambda x: x.lower())

    def safe_rename_images(self, folder, image_list, rename_format):
        if not image_list:
            return []
        total = len(image_list)
        width = len(str(total))
        expected_names = []
        for i, old in enumerate(image_list, 1):
            if self.stop_flag and self.stop_flag.is_set():
                self.output("用户停止，重命名中断", 'error')
                break
            name, ext = os.path.splitext(old)
            fmt = rename_format
            def replace_serial(match):
                format_spec = match.group(1)
                if format_spec is None:
                    return f"{i:0{width}d}"
                else:
                    try:
                        return f"{i:{format_spec}}"
                    except ValueError:
                        return f"{i:0{width}d}"
            fmt = re.sub(r'\{序号(?::([^}]+))?\}', replace_serial, fmt)
            fmt = fmt.replace('{原文件名}', name)
            if not fmt.endswith(ext):
                fmt += ext
            expected_names.append(fmt)
        used_targets = set()
        for i in range(len(expected_names)):
            orig = expected_names[i]
            new = orig
            counter = 1
            while new in used_targets:
                base, ext = os.path.splitext(orig)
                new = f"{base} ({counter}){ext}"
                counter += 1
            used_targets.add(new)
            expected_names[i] = new
        temp_names = []
        self.output("第一步：重命名为临时名称...", 'info')
        for idx, old in enumerate(image_list):
            if self.stop_flag and self.stop_flag.is_set():
                break
            old_path = os.path.join(folder, old)
            while True:
                temp = f"temp_{uuid.uuid4().hex}_{old}"
                temp_path = os.path.join(folder, temp)
                if not os.path.exists(temp_path):
                    break
            try:
                os.rename(old_path, temp_path)
                temp_names.append(temp)
            except:
                pass
            if self.progress:
                self.progress(30 + (idx+1)/total * 30)
        self.output("第二步：重命名为最终名称...", 'info')
        final_names = []
        for idx, (temp, expected) in enumerate(zip(temp_names, expected_names[:len(temp_names)])):
            if self.stop_flag and self.stop_flag.is_set():
                break
            temp_path = os.path.join(folder, temp)
            target_path = os.path.join(folder, expected)
            try:
                os.rename(temp_path, target_path)
                final_names.append(expected)
            except OSError as e:
                if e.errno == 183:
                    base, ext = os.path.splitext(expected)
                    counter = 1
                    while True:
                        new_target = f"{base} ({counter}){ext}"
                        new_target_path = os.path.join(folder, new_target)
                        if not os.path.exists(new_target_path):
                            break
                        counter += 1
                    try:
                        os.rename(temp_path, new_target_path)
                        final_names.append(new_target)
                    except:
                        pass
            if self.progress:
                self.progress(60 + (idx+1)/total * 40)
        return final_names

    def move_images_to_target(self, source, image_names, target):
        if not image_names:
            return
        os.makedirs(target, exist_ok=True)
        moved = 0
        for fname in image_names:
            if self.stop_flag and self.stop_flag.is_set():
                break
            src = os.path.join(source, fname)
            dst = os.path.join(target, fname)
            if not os.path.exists(src):
                continue
            try:
                shutil.move(src, dst)
                moved += 1
                self.processed_count += 1
            except:
                pass
        self.output(f"共移动 {moved} 个文件", 'info')

    def process(self, source, target, size_limit=200, enable_move=True, rename_format="{序号:03d}.jpg"):
        self.processed_count = 0
        if self.status:
            self.status("处理中...")
        if not os.path.isdir(source):
            self.output("错误：源文件夹不存在", 'error')
            return 0, 0
        deleted_small = self.delete_small_images(source, size_limit)
        images = self.collect_remaining_images(source)
        final_names = self.safe_rename_images(source, images, rename_format)
        if enable_move and target and source != target:
            self.move_images_to_target(source, final_names, target)
        else:
            self.processed_count = len(final_names)
        self.output("全部完成！", 'info')
        return self.processed_count, deleted_small