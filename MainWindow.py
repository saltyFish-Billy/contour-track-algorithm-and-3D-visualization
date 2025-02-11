from PyQt5.QtCore import QRect
from PyQt5.QtWidgets import QMainWindow,QWidget,QMdiArea,QMenuBar,QMenu,QToolBar,QStatusBar,QAction,QVBoxLayout
import tkinter as tk
from tkinter import filedialog
from PyQt5.QtGui import QIcon
from ReadData import readPoints
from TVTKWindow import TVTKQWidget
from SetContourNum import SetContourDialog


class MainWindow(QMainWindow):
    def __init__(self):  # 初始化界面
        super(MainWindow, self).__init__()  # 调用父类QMainWindow的构造函数
        self.setupUi(self)  # 建立UI界面

    def setupUi(self, MainWindow):  # 设计界面
        MainWindow.resize(1200, 900)  # 设置窗口大小
        MainWindow.setWindowTitle("可视化主窗口")  # 设置窗口名称
        self.centralwidget = QWidget(MainWindow)  # 定义中心控件
        MainWindow.setCentralWidget(self.centralwidget)  # 将中心控件放入主窗口中
        self.mdiArea = QMdiArea(self.centralwidget)  # 定义窗口显示区
        self.mdiArea.setGeometry(QRect(-1, -1, 2000, 1000))  # 定义窗口显示区的大小
        self.menubar = QMenuBar(MainWindow)  # 定义菜单栏
        self.file = QMenu(self.menubar)  # 定义file按钮
        self.file.setTitle("文件")  # 设置file按钮名称

        MainWindow.setMenuBar(self.menubar)  # 添加菜单栏到窗口
        self.toolbar = QToolBar(MainWindow)  # 定义工具栏
        MainWindow.addToolBar(self.toolbar)  # 添加工具栏到窗口
        self.statusbar = QStatusBar(MainWindow)  # 定义状态栏
        MainWindow.setStatusBar(self.statusbar)  # 添加状态栏到窗口
        self.actionOpen = QAction(MainWindow)  # 定义动作(子按钮)
        self.actionOpen.setText("Open")  # 设置子按钮名称

        self.file.addAction(self.actionOpen)  # 将动作(子按钮)添加到指定按钮下
        self.menubar.addAction(self.file.menuAction())  # 将菜单栏按钮添加到菜单栏

        self.actionOpen.triggered.connect(self.OpenSlot)  # 将动作(信号)与槽函数关联

        self.actionContourMapping = QAction(QIcon("./image/draw_contour.png"), "Draw Contour", self)
        self.toolbar.addAction(self.actionContourMapping)
        self.actionContourMapping.triggered.connect(self.ContourMappingSlot)

    def OpenSlot(self):  # 打开文件槽函数
        root = tk.Tk()  # 创建一个Tkinter.Tk()实例
        root.withdraw()  # 将Tkinter.Tk()实例隐藏
        self.fileName = filedialog.askopenfilename()  # 设置打开文件对话框
        if (self.fileName == ""):  # 名称为空
            return
        self.x, self.y, self.z, self.data = readPoints(self.fileName)

    def ContourMappingSlot(self):
        if self.fileName == "":
            return

        self.tvtk_widget = TVTKQWidget(self.x, self.y, self.z)  # 定义TVTK控件
        self.tvtkWin = QMainWindow()  # 定义TVTK窗口
        self.tvtkWin.setWindowTitle("TVTK窗口")  # 设置窗口标题
        self.tvtkWin.setCentralWidget(self.tvtk_widget)  # 将TVTK控件放入TVTK窗口
        self.mdiArea.addSubWindow(self.tvtkWin)  # 将TVTK窗口作为主窗口的子窗口
        self.tvtkWin.show()  # 显示TVTK窗口
        # 添加等高线级数设置按钮
        self.tvtk_toolbar = QToolBar()
        self.tvtkWin.addToolBar(self.tvtk_toolbar)
        self.actionSetContour = QAction(QIcon("./image/set_Contour.bmp"), "Set Contour", self.tvtkWin)
        self.tvtk_toolbar.addAction(self.actionSetContour)

        # 将等高线级数设置按钮与槽函数相关联
        self.actionSetContour.triggered.connect(self.SetContourSlot)


    def SetContourSlot(self):
        self.tvtk_widget.timer.stop()  # 计时器停止
        self.tvtk_setContour = SetContourDialog()  # 根据类创建交互式设置界面对象
        self.tvtk_setContour._signal.connect(self.tvtk_widget.getContour)#这里会传递信号、恢复计时器并且关掉自己
        self.tvtk_setContour.show()  # 调出界面,此句执行结束后传递 pyqtsingal 对象 _signal 到TVTK中
