# -*- coding: utf-8 -*-
import os
import sys
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.core.window import Window

# 复用你的业务逻辑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.link_rules import LinkRules, process_links_lines
from core.image_processor import ImageProcessor
from core.config import load_config, save_config, DEFAULT_DRIVE, DEFAULT_ROOT_DIR, DEFAULT_SUB_DIR, DEFAULT_SERIES, DEFAULT_SIZE_LIMIT, DEFAULT_RENAME_FORMAT

Window.size = (400, 700)

class LinkTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=5, padding=10, **kwargs)
        self.add_widget(Label(text='📥 原始链接（每行一条）:', size_hint_y=0.08, halign='left'))
        self.input_text = TextInput(multiline=True, size_hint_y=0.25, font_size=12)
        self.add_widget(self.input_text)
        btn_row = BoxLayout(size_hint_y=0.1, spacing=5)
        btn_row.add_widget(Button(text='处理', on_press=self.process_links))
        btn_row.add_widget(Button(text='清空', on_press=lambda x: setattr(self.input_text, 'text', '')))
        self.add_widget(btn_row)
        self.add_widget(Label(text='✨ 处理结果:', size_hint_y=0.08, halign='left'))
        self.output_text = TextInput(multiline=True, size_hint_y=0.25, readonly=True, font_size=12)
        self.add_widget(self.output_text)
        self.stats_label = Label(text='等待处理...', size_hint_y=0.08)
        self.add_widget(self.stats_label)

    def process_links(self, instance):
        raw = self.input_text.text.strip()
        if not raw:
            return
        lines = [l for l in raw.splitlines() if l.strip()]
        if not lines:
            return
        try:
            res, stats = process_links_lines(lines)
        except Exception as e:
            self.output_text.text = f"错误: {e}"
            return
        self.output_text.text = "\n".join(res)
        self.stats_label.text = f"原始:{stats['original_count']} | 删除:{stats['deleted']} | 总修改:{stats['total_modified']}"

class ImageTab(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=5, padding=10, **kwargs)
        self.config = load_config()
        self.is_running = False
        form = GridLayout(cols=2, size_hint_y=0.6, spacing=3)
        form.add_widget(Label(text='盘符:'))
        self.drive_input = TextInput(text=self.config.get('drive', DEFAULT_DRIVE))
        form.add_widget(self.drive_input)
        form.add_widget(Label(text='根目录:'))
        self.root_input = TextInput(text=self.config.get('root_dir', DEFAULT_ROOT_DIR))
        form.add_widget(self.root_input)
        form.add_widget(Label(text='子目录:'))
        self.sub_input = TextInput(text=self.config.get('sub_dir', DEFAULT_SUB_DIR))
        form.add_widget(self.sub_input)
        form.add_widget(Label(text='系列名:'))
        self.series_input = TextInput(text=self.config.get('series', DEFAULT_SERIES))
        form.add_widget(self.series_input)
        form.add_widget(Label(text='大小阈值(KB):'))
        self.size_input = TextInput(text=str(self.config.get('size_limit', DEFAULT_SIZE_LIMIT)))
        form.add_widget(self.size_input)
        form.add_widget(Label(text='重命名格式:'))
        self.format_input = TextInput(text=self.config.get('rename_format', DEFAULT_RENAME_FORMAT))
        form.add_widget(self.format_input)
        self.add_widget(form)
        btn_row = BoxLayout(size_hint_y=0.08, spacing=5)
        self.start_btn = Button(text='▶ 开始处理', on_press=self.start_processing)
        btn_row.add_widget(self.start_btn)
        btn_row.add_widget(Button(text='保存配置', on_press=self.save_config))
        self.add_widget(btn_row)
        self.progress_bar = ProgressBar(value=0, max=100, size_hint_y=0.05)
        self.add_widget(self.progress_bar)
        self.add_widget(Label(text='📋 日志:', size_hint_y=0.05, halign='left'))
        self.log_text = TextInput(multiline=True, size_hint_y=0.3, readonly=True, font_size=11)
        self.add_widget(self.log_text)

    def save_config(self, instance=None):
        self.config['drive'] = self.drive_input.text
        self.config['root_dir'] = self.root_input.text
        self.config['sub_dir'] = self.sub_input.text
        self.config['series'] = self.series_input.text
        try:
            self.config['size_limit'] = int(self.size_input.text)
        except:
            pass
        self.config['rename_format'] = self.format_input.text
        save_config(self.config)
        self.log('配置已保存', 'info')

    def log(self, msg, tag='info'):
        Clock.schedule_once(lambda dt: self._log_main(msg, tag))

    def _log_main(self, msg, tag):
        self.log_text.text += f"{msg}\n"
        self.log_text.cursor = (0, len(self.log_text.text))

    def start_processing(self, instance):
        if self.is_running:
            self.log('已有任务运行中', 'error')
            return
        self.config['drive'] = self.drive_input.text
        self.config['root_dir'] = self.root_input.text
        self.config['sub_dir'] = self.sub_input.text
        self.config['series'] = self.series_input.text
        try:
            self.config['size_limit'] = int(self.size_input.text)
        except:
            pass
        self.config['rename_format'] = self.format_input.text
        drive = self.config['drive'].strip()
        root = self.config['root_dir'].strip()
        sub = self.config['sub_dir'].strip()
        series = self.config['series'].strip()
        if drive and not drive.endswith('\\') and not drive.endswith(':'):
            drive += '\\'
        parts = [drive] if drive else []
        if root:
            parts.append(root)
        if sub:
            parts.append(sub)
        if series:
            parts.append(series)
        target = '\\'.join(parts) if parts else ''
        source_folders = self.config.get('source_folders', [])
        if not source_folders:
            self.log('⚠️ 请先在配置中添加源文件夹', 'error')
            return
        self.is_running = True
        self.start_btn.disabled = True
        self.progress_bar.value = 0
        self.log_text.text = ''
        self.log('✨ 开始批量处理...', 'info')
        threading.Thread(target=self._process_worker, args=(source_folders, target), daemon=True).start()

    def _process_worker(self, source_folders, target):
        total = len(source_folders)
        size_limit = self.config.get('size_limit', DEFAULT_SIZE_LIMIT)
        rename_format = self.config.get('rename_format', DEFAULT_RENAME_FORMAT)
        for idx, src in enumerate(source_folders):
            if not os.path.isdir(src):
                self.log(f'❌ 文件夹不存在，跳过: {src}', 'error')
                continue
            self.log(f'📁 处理: {src}', 'info')
            def progress_callback(v):
                Clock.schedule_once(lambda dt, val=v: self._update_progress(val), 0)
            def output_callback(msg, tag='info'):
                self.log(msg, tag)
            processor = ImageProcessor(output_callback, progress_callback, None)
            count, deleted = processor.process(src, target, size_limit, True, rename_format)
            self.log(f'   → 处理 {count} 张图片，删除 {deleted} 张', 'info')
            Clock.schedule_once(lambda dt, val=((idx+1)/total)*100: self._update_progress(val), 0)
        Clock.schedule_once(self._finish_processing, 0)

    def _update_progress(self, value):
        self.progress_bar.value = value

    def _finish_processing(self, dt):
        self.is_running = False
        self.start_btn.disabled = False
        self.log('✅ 所有文件夹处理完成！', 'info')

class MainApp(App):
    def build(self):
        root = BoxLayout(orientation='vertical')
        root.add_widget(Label(text='图片处理工具', size_hint_y=0.07, font_size=20))
        tab_panel = TabbedPanel(size_hint_y=0.93, do_default_tab=False)
        link_tab = TabbedPanelItem(text='链接处理')
        link_tab.add_widget(LinkTab())
        tab_panel.add_widget(link_tab)
        image_tab = TabbedPanelItem(text='图片处理')
        image_tab.add_widget(ImageTab())
        tab_panel.add_widget(image_tab)
        root.add_widget(tab_panel)
        return root

if __name__ == '__main__':
    MainApp().run()