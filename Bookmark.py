#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import sublime, sublime_plugin
import time
import os


"""

目前已经的问题:

- 第一次打开大文件可能存在延时

初步计划:

- 导入 emacs 的 bookmark 
- 设置和打开 bookmark 输名字的时候可以利用 on_change 实现自动补齐。

hick; hickwu@qq.com

"""



class BMSetting:
    """
    配置文件操作封装
    """
    # 默认操作的文件
    file = ""
    # setting
    settings = None
    ### 保存 bookmark list 的 key; 同时作为 region 前缀
    bmkey = "bm_list"
    
    ### 构造函数
    def __init__(self, file = "Bookmark.data"):
        self.file = file
        self.settings = sublime.load_settings(self.file)
    
    ### 获取某个设置项 key 的值
    def get(self, key):
        return self.settings.get(key, '')

    ### 保存一个设置项的 key 值
    def set(self, key, value):
        key = str(key).strip()
        self.settings.set(key, value)
        return sublime.save_settings(self.file)

    ### 添加一个名字的 bookmark, file 是文件名, a b 分别是 region 的俩个偏移值
    def addbm(self, bookmark_name, file, a, b, other = {}):
        bm_list = self.get(self.bmkey)
        if len(bm_list) < 1:
            bm_list = {}
        # 不允许有空格
        bookmark_name = str(bookmark_name).strip()
        bm_list[bookmark_name] = { "file" : str(file), "a":str(a), "b":str(b) }
        # 保存回去
        return self.set(self.bmkey, bm_list)

    ###  获得 bookmark 的信息，传递空参数则返回全部 bookmark
    def getbm(self, bookmark_name = ""):
        bookmark_name = str(bookmark_name).strip()
        bm_list = self.get(self.bmkey)

        if len(bookmark_name) < 1:
            return bm_list

        if len(bm_list) < 1:
            bm_list = {}
        if bookmark_name in bm_list:
            bm = bm_list[bookmark_name]
        else:
            bm = {}
        return bm


### 测试监听事件 
class BookmarkEvent(sublime_plugin.EventListener):
    """
    其实最好参考 API 和这里全部都定义 https://github.com/titoBouzout/BufferScroll/blob/master/BufferScroll.py
    """
    # restore on load for new opened tabs or previews: tab 被打开或者预览的时候加载 region
    def on_load(self, view):
        icon = "Packages/Theme - Default/tool_tip_background.png"
        ### 获得保存的 region 信息: 属于当前文件才加载
        bm_list = BMSetting().getbm()
        for bookmark_name in bm_list:
            info = bm_list[bookmark_name]
            if view.file_name() == info["file"]:
                sublime.status_message('BookmarkEvent!!!! @ ' + time.strftime("%Y-%m-%d %X - ") + info["file"])
                # 属于本文件的，创建 region
                region_mark = sublime.Region(int(info['a']), int(info['b'])) # 自己定义 mark
                view.add_regions(BMSetting.bmkey + bookmark_name, [region_mark], BMSetting.bmkey + bookmark_name,
                    icon, sublime.HIDDEN | sublime.PERSISTENT)

    # 关闭的时候的事件，  pre_close 也可以考虑检查下
    def on_pre_close(self, view):
        ### 这里要判断，有需要保存的 region 才去操作

        # if  len(view.get_regions(mark_id)) < 1:
        #     sublime.status_message('OnCloseNoRegions @ ' + time.strftime("%Y-%m-%d %X @ " + str(mark_id) ))
        #     return

        # region_mark = view.get_regions(mark_id)[0]

        # sublime.status_message('BookmarkEvent @ ' + time.strftime("%Y-%m-%d %X - ") + mark_id)

        # settings = sublime.load_settings(BookmarkConst['data_file'])
        # ########???? 知道怎么读取一个设置的子项，但是不知道怎么写， 直接赋值一个字典不行，先保存俩值好了
        # set_value = {"file": view.file_name(), "region_a": region_mark.a, "region_b": region_mark.b}
        # settings.set(mark_id, set_value)
        # # settings.set(mark_id + ".file", str(view.file_name()) )
        # # settings.set(mark_id + ".region", str(region_mark))
        # sublime.save_settings(BookmarkConst['data_file'])
        return




class BookmarkSetCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # 用户交互输入面板
        self.view.window().show_input_panel('set bookmark name', '', self.bookmark_input_name, 'on_change', None)

        sublime.status_message('BookmarkSetCommand@ ' + time.strftime("%Y-%m-%d %X"))

    ### 处理输入的书签名
    def bookmark_input_name(self, name):
        name = str(name)
        name = name.strip()
        if len(name) < 1:
            sublime.status_message("please input the bookmark name")
            return true

        region_mark = self.view.sel()[0]

        ### 设置
        # region_mark = sublime.Region(222, 222) # 自己定义 mark
        icon = "Packages/Theme - Default/tool_tip_background.png"
        self.view.add_regions(BMSetting.bmkey + name, [region_mark], BMSetting.bmkey + name,
            icon, sublime.HIDDEN | sublime.PERSISTENT)
        sublime.status_message('Test111 @ ' + time.strftime("%Y-%m-%d %X @ " + str(region_mark) ))

        ### 保存
        BMSetting().addbm(name, self.view.file_name(), region_mark.a, region_mark.b)
        sublime.status_message("set bookmark done for " + name)


### 避免文件没加载完成，延期执行
def test_timeout(curr_view, regions):
    if len(regions) > 0:
        # set bookmark to a center of the screen
        curr_view.show_at_center(regions[0])

        # set cursor to the proper position
        curr_view.sel().clear()
        curr_view.sel().add(regions[0])


class BookmarkGotoCommand(sublime_plugin.WindowCommand):
    """
    因为在没有打开任何 view 的时候没有 TextCommand 可取，这里必须继承 WindowCommand 以免没有打开 view 时报错
    注意 WindowCommand 的 run 不能有第二个参数
    """
    def run(self):
        # 用户交互输入面板
        self.window.show_input_panel('goto bookmark name', '', self.bookmark_input_name, 'on_change', None)
        sublime.status_message('BookmarkSetCommand @ ' + time.strftime("%Y-%m-%d %X"))

    ### 处理输入的书签名
    def bookmark_input_name(self, name):
        name = str(name)
        name = name.strip()
        if len(name) < 1:
            sublime.status_message("please input the bookmark name")
            return 
        ### 取出保存的配置信息，确定是否当前文件，不是当前文件则打开
        curr_view = self.window.active_view()
        setting_info = BMSetting().getbm(name)

        ### 如果没找到，则提示
        if len(setting_info) < 1:
            sublime.status_message("find no bookmark named: " + name)
            return 

        ### 着时候可能没有活动窗口
        if curr_view == None or curr_view.file_name() != setting_info['file']:
            self.window.open_file(setting_info['file'])
            curr_view = self.window.active_view()
            a = setting_info['a']
            b = setting_info['b']

            # sublime.status_message("debug" + str(a) +  ":" + str(b))

            regions = [sublime.Region(int(a), int(b) )]

            ###TODO 后续看使用情况如何，可以考虑根据打开文件的大小决定延迟时间
            sublime.set_timeout(lambda: test_timeout(curr_view, regions), 1000)
        else:
            regions = curr_view.get_regions(BMSetting.bmkey + name)

        ### 执行跳转
        if len(regions) > 0:
            # set bookmark to a center of the screen
            curr_view.show_at_center(regions[0])

            # set cursor to the proper position
            curr_view.sel().clear()
            curr_view.sel().add(regions[0])

        return


"""
回到 windows 下的资源管理器
"""
class GotoWindowsExplorerCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        curr_path = os.path.dirname(self.view.file_name())
        os.popen("explorer /e," + curr_path)