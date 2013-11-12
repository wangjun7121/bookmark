#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import sublime, sublime_plugin
import webbrowser
import time
import os

# import wxpython

"""

目前已经的问题:

- 第一次打开大文件可能存在延时

初步计划:

- 记住使用频率，默认打开的时候就在状态栏提示最常用的和最近打开的
- 导入 emacs 的 bookmark ~hick
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

    ### 保存当前的配置的操作
    def save(self):
        return sublime.save_settings(self.file)

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

    BOOKMARK_REG = "~[A-Za-z0-9]+"
    MAX_HIGHLIGHT_ONE_VIEW = 200
    bookmarks_for_view = {}
    ### 保存每个 view 的 scope 列表
    scopes_for_view = {}
    ignored_views = []

    def on_selection_modified(self, view):
        ### 只在 toc. 系列的索引 view 中生效
        view = sublime.active_window().active_view()
        name = view.name()
        if len(name) > 4:
            if 'toc.' == name[0:4]:
                # 获得鼠标点击处的文本
                line_sel = view.line(view.sel()[0])
                line_txt = view.substr(line_sel)
                # 尽可能还原能匹配原原本的值: 后续考虑用 bookmark 式的临时 region 会方便很多
                line_txt = r"\n%s" % line_txt
                # title 中出现 () 等正则特殊符号则需要转义
                line_txt = line_txt.replace('(', '\(').replace(')', '\)')
                # 确保文件打开(如果文件没打开，第一次没有渲染完，需要再点击一次，懒得改了，挺合理)
                # 曾经出现点一次第二组的 view 触发两次本事件，焦点跳走以后就只触发一次了
                sublime.active_window().focus_group(0)
                tocedview = sublime.active_window().open_file(name[4:])
                # 使居中
                regions = tocedview.find_all(line_txt)
                tocedview.show_at_center(regions[0])
                view.sel().clear()
                view.sel().add(regions[0])
                # print(view.substr(line_sel))


    #             # print("%s,%s,%s,%s" % (time.strftime('%Y-%m-%d %X'), view.name(), view.sel()[0], line_txt))

        


    # # 鼠标点击下之前
    # def on_pre_mouse_down(self, args):
        # print("on pre-click!", args)

    # 鼠标点击下以后: 之前装了 MouseEventListener 才有用
    # def on_post_mouse_down(self, point):
    #     print(self)
    #     pass

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
        # 高亮书签
        self.highlight_bookmark(view)

    # 关闭的时候的事件，  pre_close 也可以考虑检查下
    def on_pre_close(self, view):
        # 经过测试确认，发现一般想删还删不了：剪切走也会自动移动
        self.save_bookmark(view)

    # 保存文件的时候也保存 bookmark
    def on_post_save(self, view):
        self.save_bookmark(view)

    # 修改文本的事件
    def on_modified(self, view):
        self.get_input(view)    
        self.highlight_bookmark(view)    

    def on_close(self, view):
        ###hick 好像是清理变量？没完全看明白为什么需要清理？ 避免关闭文件浪费内存？
        for map in [self.bookmarks_for_view, self.scopes_for_view, self.ignored_views]:
            if view.id() in map:
                del map[view.id()]

    ### test for input
    def get_input(self, view):
        # curr_view = self.window.active_view()
        curr_view = view 
        selection = curr_view.sel()[0]
        # word_region = curr_view.word(selection.a)
        ### 获得 word 单词： 定义似乎是连续字母汉字下划线 
        word = curr_view.substr(selection.a - 1)   
        # print(word == "\t") #不奏效
        # print(word)     #hick

    def highlight_bookmark(self, view): 
        ###hick 如果在忽略的列表则不渲染
        if view.id() in self.ignored_views: 
            return
        sublime.status_message('highlight_bookmark' + time.strftime("%Y-%m-%d %X"))
        # 先去掉之前的高亮，再重新查找出来
        self.rmhighlight_bookmark(view)
        bookmarks = view.find_all(self.BOOKMARK_REG)
        ###hick 当 bookmarks 数量过多时，把当前视图列为不高亮的 view
        if len(bookmarks) > self.MAX_HIGHLIGHT_ONE_VIEW:
            sublime.status_message("the count of bookmarks of this view is too much")
            self.ignored_views.append(view.id())
            return
        # 记录 bookmark 的 view 以及具体位置
        self.bookmarks_for_view[view.id()] = bookmarks
        # 没完全理解， 貌似是把所有 bookmark 的范围 scope 保存到 scope_map
        scope_map = {}
        for bm in self.bookmarks_for_view[view.id()]:
            scope_name = view.scope_name(bm.a)
            scope_map.setdefault(scope_name, [])
            scope_map[scope_name] += [sublime.Region(pos, pos) for pos in range(bm.a, bm.b)]

        for scope_name in scope_map:
            ###hick 加下划线
            ###hick 下划线颜色由 flags 前面的参数决定，可以是 
            ### string comtment invalid  keyword entity constant storage support variable 
            ### 白色    灰色    深橙-for 深橙-for   --- 貌似颜色是跟主体相关的
            ### 这里有相关颜色的定义 http://tmtheme-editor.herokuapp.com/ https://github.com/aziz/tmtheme-editor
            ###hick icon 为行号旁边的图标，还可以是  dot, circle, bookmark 和 cross.

            ### example ~test_timeout
            ### example ~doc

            view.add_regions(u'visitable-bookmarks ' + scope_name, scope_map[scope_name], "comtment", icon="dot", flags=sublime.DRAW_EMPTY_AS_OVERWRITE)
        self.scopes_for_view[view.id()] = scope_map.keys()

    def rmhighlight_bookmark(self, view):
        if view.id() in self.scopes_for_view:
            for scope_name in self.scopes_for_view[view.id()]:
                view.erase_regions(u'visitable-bookmarks ' + scope_name)
 
    ### 保存当前 view 的书签
    def save_bookmark(self, view): 

        ### 计时统计下消耗时间看看
        start_time = time.time()
        ### 获得保存的 region 信息: 属于当前文件才保存
        bm_list = BMSetting().getbm()
        for bookmark_name in bm_list:
            info = bm_list[bookmark_name]
            if view.file_name() == info["file"]:
                # 获得最新位置以后保存： 经实测是删除不了的，万一有不存在，不保存就是
                region = view.get_regions(BMSetting.bmkey + bookmark_name)
                # 如果没找到则跳过： 确信过删除不了的，以后考虑单独删除
                if len(region) < 1:
                    continue
                bm_list[bookmark_name]['a'] = region[0].a
                bm_list[bookmark_name]['b'] = region[0].b

        BMSetting().set(BMSetting.bmkey, bm_list)
        # 保存的动作
        cost_time = time.time() - start_time
        return 



class BookmarkSetCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # 用户交互输入面板
        self.view.window().show_input_panel('set bookmark name', '', self.after_input_name, 'on_change', None)

        sublime.status_message('BookmarkSetCommand@ ' + time.strftime("%Y-%m-%d %X"))

    ### 处理输入的书签名
    def after_input_name(self, name):
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

        ### 列表中增加以便及时提醒: 清空以后载入时会自动全 load
        BookmarkGotoCommand.bm_name_list = []

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
    # 在用户输入之前准备好可选书签列表
    bm_name_list = []
    # 记录用户上次输入
    last_input = ""
    

    # def run(self, edit, ref=None,val=None):
    def run(self, ref=None):

        ### 如果书输入跳转的方式
        if ref == "input":
            # 用户交互输入面板
            self.window.show_input_panel('goto bookmark name', '', self.after_input_name, self.on_input_change, None)
            sublime.status_message('BookmarkSetCommand @ ' + time.strftime("%Y-%m-%d %X"))

            # 获得所有 bookmark name 列表, 一边自动提示功能
            if len(self.bm_name_list) < 1:
                bm_list = BMSetting().getbm()
                for bm_name in bm_list:
                    self.bm_name_list.append(bm_name)
        ### 打开当前光标所在位置的书签: 跟之前的高亮不大一样，这里只匹配书签名，没有 @ 也可以。
        else:
            #example ~hick ~python ~doc
            curr_view = self.window.active_view()
            selection = curr_view.sel()[0]
            word_region = curr_view.word(selection.a)
            ### 获得 word 单词： 定义似乎是连续字母汉字下划线
            word = curr_view.substr(word_region)
            ### 这里限定独立文字，也就是两边都是空格等非文字字符才算书签，不需要排除汉字和下划线干扰
            ### 如果当前单词是某个书签，则直接跳转 hick
            bookmark = BMSetting().getbm(word)
            # 有找到对应的 bookmark 信息就跳转
            if len(bookmark) > 1:
                self.after_input_name(word)
            else:
                sublime.status_message("!!! get no bookmark for current word: %s" % word)

            ###test hickpad
            # print(bookmark)
            # print(len(bookmark)) 
            # print(BookmarkGotoCommand.after_input_name(self, word)) 
            ### 判断选区是否为空: word-hick_hick!34345(6d)
            #selection.empty()
            ### 返回光标所在位置的单词的 region
            # print(self.view.word(selection.a))
            return


    ### 处理输入的书签名
    def after_input_name(self, name):
        name = str(name)
        name = name.strip()
        if len(name) < 1:
            sublime.status_message("please input the bookmark name")
            return 
        ### 取出保存的配置信息，确定是否当前文件，不是当前文件则打开
        curr_view = self.window.active_view()
        setting_info = BMSetting().getbm(name)

        ### 如果没找到，则全文匹配第一个符合的
        if len(setting_info) < 1:
            for bm in self.bm_name_list:
                if bm.find(name) >= 0:
                    setting_info = BMSetting().getbm(bm)
                    break


        # 还是没有则提示没找到
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
            sublime.set_timeout(lambda: test_timeout(curr_view, regions), 500)
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


    ### 输入变化事件
    def on_input_change(self, text):
        # 如果发现用户最新输入的是一个数字，则去掉该数字以后继续进行匹配
        if len(text) > 0:
            self.last_input = text[-1]
            if self.last_input >= "0" and self.last_input <= "9":
                text = text[0:-1]
            
        # 匹配用户输入
        matchstr = " ***** select by number *****  "
        i = 1

        matchs = []
        for bm in self.bm_name_list:
            if bm.find(text) >= 0:
                matchs.append(bm)

        # for m in matchs:
                if str(i) == self.last_input:
                    self.after_input_name(bm)
                    break

                # 超过 9 个的就不显示了，只加省略号
                if i > 9:
                    matchstr += " ... "
                    continue
                # 如果有超过 20 个就直接不管了
                if i > 20:
                    break

                matchstr += str(i) + ":" + bm + "  "
                i += 1

        ###hicktodo 因为依赖状态栏，这里最好是判断下状态栏状态，没有显示的话先显示，timeout 几秒以后关闭都 ok
        sublime.status_message(matchstr)


"""
回到 windows 下的资源管理器
"""
class GotoWindowsExplorerCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        curr_path = os.path.dirname(self.view.file_name())
        os.popen("explorer /e," + curr_path)


"""
调用 chrome 打开当前 view
"""
class GotoChromeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        chromePath = 'D:\\Program\\Chrome\\chrome.exe'
        webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chromePath))
        webbrowser.get('chrome').open_new_tab(self.view.file_name())

"""
调试命令
"""
class TocViewCommand(sublime_plugin.TextCommand):
    def run(self, edit, opt = None):
        # 如果已经有俩列了，则表示合成一列
        win = self.view.window()

        if win.num_groups() > 1:
            params = {"cols": [0.0, 1.0],"rows": [0.0, 1.0], "cells": [[0, 0, 1, 1]]}
            win.set_layout(params)
            # 关闭 toc 的 view ，要不然每次打开一次多一个: 官方没有提供 view 的关闭方法，下面是折衷的
            # 意外的"动画"效果，就不改造先关再改变布局了
            for v in win.views():
                vname = v.name()
                if 'toc.' == vname[0:4]:
                    win.focus_view(v)
                    v.set_scratch(True) # 这行放弃所有修改
                    win.run_command("close_file")


        else:
            win.set_layout({"cols": [0.0, 0.8, 1.0], "rows": [0.0, 1.0], "cells": [[0, 0, 1, 1], [1, 0, 2, 1]]})
            # 聚焦到 toc 窗口以后创建 buffer
            win.focus_group(1)

            # 查找到所有 title
            # 后续可以走 view.symbols() 获得标题而不是靠以前的 # 匹配的方式
            insert_txt = ""
            title_sels = self.view.find_all("[\n]+#.*")
            for sel in title_sels:
                # 根据传递的参数 opt 决定显示的层次: #出现次数超过 opt+1 个就需要忽略
                curr_title = self.view.substr(sel).strip()
                invalid_str = '#'*(1 + int(opt))
                if curr_title.find(invalid_str) > -1:
                    continue
                
                insert_txt = "%s\n%s" % (insert_txt, curr_title)

            # 插入到编辑器
            tocview = win.new_file()
            ### 在被索引文件被切换走，甚至关闭的时候，也能跳转到，这里记录打开文件名，比如 toc.f:/hick.md
            # 在文件被切换走以后， window.open_file(filename) 能切换或者重新打开文件
            tocview.set_name('toc.%s' % self.view.file_name())
            tocview.insert(edit, 0, insert_txt)
            tocview.end_edit(edit)


            # 不允许编辑
            # tocview.set_read_only(True)
                
            # print("debug@%s columns done: %s " % (time.strftime("%Y-%m-%d %X"), title_sels))

            # 确保聚焦到编辑
            # win.focus_group(0)

        

