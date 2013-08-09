#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
目前已经的问题:

- 没有打开任何窗口的时候，大概是没有窗口对象，所以 f12 无效

初步计划:

- 保存格式还只有文件名，需要能定位到行，格式参考 emacs bookmark
- 导入 emacs 的 bookmark 
- 设置和打开 bookmark 输名字的时候可以利用 on_change 实现自动补齐。
- 要学 emacs 还需要把具体的行数以及前后的文本记下来(这标记若干个字符就够了)

"""




import sublime, sublime_plugin
import time

markPreffix = "delphi_style_bookmark_"

### 全局变量
Bookmark = {
    "data_file": "Bookmark.data",
}


### 每一个类名都可以关联到快捷键设置的  command 属性  
class BookmarkTestCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.window.show_input_panel('set bookmark name', '', self.bookmark_input_name, 'on_change', None)

        # 加载 bookmark 数据
        sublime.status_message('BookmarkTestCommand @ ' + time.strftime("%Y-%m-%d %X"))


    ### 处理输入的书签名
    def bookmark_input_name(self, name):
        name = str(name)
        name = name.strip()
        if len(name) < 1:
            sublime.status_message("please input the bookmark name")
            return true

        self.settings = sublime.load_settings(Bookmark['data_file'])
        self.settings.set(name, self.window.active_view().file_name())
        sublime.save_settings(Bookmark['data_file'])
        sublime.status_message("set bookmark done for " + name)




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

        self.settings = sublime.load_settings(Bookmark['data_file'])
        self.settings.set(name, self.view.file_name())
        sublime.save_settings(Bookmark['data_file'])
        sublime.status_message("set bookmark done for " + name)




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
            return true

        self.settings = sublime.load_settings(Bookmark['data_file'])
        bookmark_file = self.settings.get(name, 'default')
        ### 如果没找到，则提示错误
        ###############################
        self.window.open_file(bookmark_file, sublime.ENCODED_POSITION)
        sublime.status_message("goto bookmark " + bookmark_file)


class OldBookmarkSetCommand(sublime_plugin.TextCommand):
    def run(self, edit, key):

        # 定义左侧的图标 --- windows 环境发现不能正常显示，为栅格线
        icon = '../Delphi Style Bookmarks/icons/'+ str(key)

        # bookmark 的 id: 自己明明的 id 即可，正好传入自己
        markId = markPreffix + str(key)

        if len(self.view.sel()) > 0:

            mark = self.view.sel()[0]

            for i in range(10):
                regions = self.view.get_regions(markPreffix+str(i))

                if len(regions) == 0:
                    continue

                m = regions[0]

                if self.adapt_region(mark).intersects(self.adapt_region(m)):
                    self.view.erase_regions(markPreffix+str(i))

                    if i == key:
                        return

            self.view.add_regions(markId,
                                [mark],
                                markId,
                                icon,
                                sublime.HIDDEN | sublime.PERSISTENT)

    def adapt_region(self, init_region):
        row, _ = self.view.rowcol(init_region.begin())

        point = self.view.text_point(row, 0)

        return sublime.Region(point, point)

class OldBookmarkGotoCommand(sublime_plugin.TextCommand):
   def run(self, edit, key):

        markId = "delphi_style_bookmark_" + str(key)

        regions = self.view.get_regions(markId)

        if len(regions) > 0:
            # set bookmark to a center of the screen
            self.view.show_at_center(regions[0])

            # set cursor to the proper position
            self.view.sel().clear()
            self.view.sel().add(regions[0])

            # 测试其他功能
            sublime.status_message("哈哈哈啊，可以了...")
