#named bookmark for sublime text

sublime text 自带的 bookmark 比较简单，不支持自定义名字的 bookmark。
默认设置下，按 F8 可以把当前光标设置书签，输入书签名以后自动保存。
按 F12 以后输入书签名即可跳转到对应文件的对应位置。

目前只支持 sublime text 3。

**特点**

1. 书签对应的文件没有打开时自动打开
2. 退出 sublime text 自动保存书签

**安装**

git clone 本代码库到 bookmark 文件夹，或者下载 zip 解压，直接放在 sublime text 
的扩展目录即可。比如 `D:\Program\Sublime3\Data\Packages\Bookmark`

**用法**

- sublime text 中打开某个文件，按 f8 下方提示框会提示输入书签名，输完回车即可。
- 按 f12 ， 下方提示框输书签名，如果打开了状态栏，会在状态栏提示匹配的书签，
  回车打开第一个匹配的书签；也可以根据状态栏提示编号，按数字键选择打开的书签
- windows 打开某个文件以后，`ctrl-e e`(按住 ctrl 不放，连按两次 e)调用资源管
  理器打开所在目录
 
**注意**

- 刚启动 sublime text 可能需要一两秒以后才能按 f12 --- sublime text 启动以后加载
插件比较慢。
- 因为选择书签的时候数字键用来选择书签，所以原则上不建议书签名中使用数字