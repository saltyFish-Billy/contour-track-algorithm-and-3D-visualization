from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import QTimer
from traits.api import *
from traitsui.api import *
from tvtk.api import tvtk
from tvtk.pyface.scene_editor import SceneEditor
from tvtk.pyface.scene import Scene
from tvtk.pyface.scene_model import SceneModel
import numpy as np
from tvtk.api import tvtk

from ColorMapping import ColorMapping
from DataStructure_contour import *


class TVTKViewer(HasTraits):  #

    scene = Instance(SceneModel, ())  # SceneModel表示TVTK的场景模型

    # 建立视图布局
    view = View(
        Item(name='scene',
             editor=SceneEditor(scene_class=Scene),  # 设置mayavi的编辑器，让它能正确显示scene所代表的模型
             resizable=True,
             ),
        resizable=True
    )


class TVTKQWidget(QWidget):
    def __init__(self, x, y, z, parent=None):
        QWidget.__init__(self, parent)
        layout = QVBoxLayout(self)  # 定义布局
        self.viewer = TVTKViewer()  # 定义TVTK界面对象
        ui = self.viewer.edit_traits(parent=self, kind='subpanel').control  # 使TVTK界面对象可以被调用
        layout.addWidget(ui)  # 将TVTK界面对象放到布局中
        # ReadData处取得原始xyz坐标列表
        self.x = x
        self.y = y
        self.z = z
        # 初始化网格行列数（根据70 * 100 的数据指定为 69 99）
        self.row = 69
        self.col = 99
        self.colors = [[200, 200, 200], [100, 100, 100], [80, 80, 80], [65, 65, 65], [50, 50, 50],
                       [20, 20, 20], [0.0, 0.0, 0.0]]
        self.plot()  # 绘制矩形网格
        self.contour_num = 0  # 等间距等值线数目
        self.custom_contour = [0]  # 自定义等值线列表
        self.contour_value = np.append(
            np.linspace((self.z.max() - self.z.min()) / (self.contour_num + 1), self.z.max(), self.contour_num,
                        endpoint=False), np.array(self.custom_contour))  # 不包含起始高度和终止高度的等值线等差数列列表
        self.flag_init()  # 对flag进行初始化，行数为等高线高程值列表的长度，列数为矩形网格的数目
        self.points = []  # 平面等高线线段实体 self.actor_contour 的几何结构, 为二维列表
        self.points_ = []  # 立体等高线线段实体 self.actor_contour_ 的几何结构, 为二维列表
        self.lines = []  # 水平及立体等高线线段的拓扑结构，为二维列表，例如 self.lines[0]存储第一条平面等高线线段的起点到终点在self.points中的编号
        self.contour_value_cur = 0  # 当前访问的等高线高程值在等高线高程值列表中的索引
        self.baseIndex = 0  # 当前等高线的第一个访问的单元网格在单元网格列表中的索引，可以理解为"根"或者"stem"
        self.leafIndex = -1  # 若等高线的第一个访问的单元网格不是等高线的端点或者该等高线封闭，则存储另一个"枝叶"访问方向
        self.rectangle_cur = 0  # 记录当前高程值下,当前访问单元网格在单元网格列表中的索引
        self.rectangle_cur_last = 0  # 记录前一个访问的四边形网格序号
        self.timer = QTimer()  # 定义计时器，来自QtCore
        self.timerID = self.timer.start(20)  # 每隔 20ms(0.02s)发送一个触发信号
        self.timer.timeout.connect(self.find_next_lineSlot)  # 每隔0.02秒触发一次self.find_next_lineSlot,注意这里不带括号
        self.form = []

    def plot(self):
        '''
        初始化四边形网格
        以网格形式绘制数据
        '''
        X, Y, Z = self.create_struct(self.x, self.y, self.z)  # 生成二维数据结构
        zmax = max(self.z)  # 求高程最大值
        zmin = min(self.z)  # 求高程最小值
        self.rectangle_list, self.rectangles = self.create_rectangle_list(X, Y, Z)  # 同时生成二维四边形网格列表和一维四边形网格列表
        row = self.row + 1
        col = self.col + 1
        # 添加点集
        points = tvtk.Points()
        points.number_of_points = row * col
        number_points = 0
        for i in range(0, row):
            for j in range(0, col):
                points.set_point(number_points, X[i][j], Y[i][j], Z[i][j])
                number_points = number_points + 1

        polyData = tvtk.PolyData()
        polyData.lines = tvtk.CellArray()
        polyData.polys = tvtk.CellArray()
        polyData.points = points

        z_new = Z.flatten()  # 转换为一维数据
        polyData.point_data.scalars = z_new

        # VTK_VERTEX, VTK_POLY_VERTEX, VTK_LINE, VTK_POLY_LINE, VTK_TRIANGLE, VTK_QUAD, VTK_POLYGON, or VTK_TRIANGLE_STRIP
        TVTK_POLY_LINE = 4
        self.form = "Grid"
        ids = tvtk.IdList()
        for i in range(0, row - 1):
            for j in range(0, col - 1):
                indexTL = i * col + j
                indexTR = i * col + j + 1
                indexBL = indexTL + col
                indexBR = indexTR + col
                ids.reset()
                # 逆时针顺序插入矩形4点序号
                ids.insert_next_id(indexTL)
                ids.insert_next_id(indexBL)
                ids.insert_next_id(indexBR)
                ids.insert_next_id(indexTR)
                ids.insert_next_id(indexTL)
                polyData.insert_next_cell(TVTK_POLY_LINE, ids)  # 插入当前网格

        polyDataMapper = tvtk.PolyDataMapper()
        polyDataMapper.set_input_data(polyData)
        polyDataMapper.scalar_range = (zmin, zmax)

        self.actor_grid = tvtk.Actor(mapper=polyDataMapper)  # grid 网格
        self.viewer.scene.add_actor(self.actor_grid)
        self.viewer.scene.render()  # 刷新界面(没有生成新的线段也可以刷新)

    def plot_surface(self):

        X, Y, Z = self.create_struct(self.x, self.y, self.z)  # 生成二维数据结构

        zmax = max(Z.flatten())
        zmin = min(Z.flatten())

        row = self.row + 1
        col = self.col + 1

        points = tvtk.Points()
        points.number_of_points = row * col
        number_points = 0
        for i in range(0, row):
            for j in range(0, col):
                points.set_point(number_points, X[i][j], Y[i][j], Z[i][j])
                number_points = number_points + 1

        polyData = tvtk.PolyData()
        polyData.lines = tvtk.CellArray()
        polyData.polys = tvtk.CellArray()
        polyData.points = points

        z_new = Z.flatten()
        polyData.point_data.scalars = z_new

        # VTK_VERTEX, VTK_POLY_VERTEX, VTK_LINE, VTK_POLY_LINE, VTK_TRIANGLE, VTK_QUAD, VTK_POLYGON, or VTK_TRIANGLE_STRIP
        TVTK_POLYGON = 7
        self.form = "Surface"
        ids = tvtk.IdList()
        for i in range(0, row - 1):
            for j in range(0, col - 1):
                indexTL = i * col + j
                indexTR = i * col + j + 1
                indexBL = indexTL + col
                indexBR = indexTR + col
                ids.reset()
                ids.insert_next_id(indexTL)
                ids.insert_next_id(indexBL)
                ids.insert_next_id(indexBR)
                polyData.insert_next_cell(TVTK_POLYGON, ids)
                ids.reset()
                ids.insert_next_id(indexTL)
                ids.insert_next_id(indexTR)
                ids.insert_next_id(indexBR)
                polyData.insert_next_cell(TVTK_POLYGON, ids)


        polyDataMapper = tvtk.PolyDataMapper()
        polyDataMapper.set_input_data(polyData)
        polyDataMapper.scalar_range = (zmin, zmax)

        colorTable = tvtk.LookupTable()
        colorTable.number_of_table_values = 256

        colors_new = ColorMapping(self.colors)
        for i in range(len(colors_new)):
            colorTable.set_table_value(i, colors_new[i][0] / 255, colors_new[i][1] / 255, colors_new[i][2] / 255)

        polyDataMapper.lookup_table = colorTable
        self.actor_surface = tvtk.Actor(mapper=polyDataMapper)
        self.actor_surface.property.ambient = 1
        self.actor_surface.property.diffuse = 0
        self.actor_surface.property.specular = 0
        self.viewer.scene.add_actor(self.actor_surface)
        self.viewer.scene.render()  # 刷新界面(没有生成新的线段也可以刷新)

    def update_actor_contour(self, line):
        '''
        更新等高线对象
        :param line: 新添加的等高线段
        :return: 平面线段和空间线段
        '''
        # 平面线段
        self.points.append([line.BeginPoint.x, line.BeginPoint.y, -0.2])
        self.points.append([line.EndPoint.x, line.EndPoint.y, -0.2])
        # 空间线段
        self.points_.append([line.BeginPoint.x, line.BeginPoint.y, line.BeginPoint.z])
        self.points_.append([line.EndPoint.x, line.EndPoint.y, line.EndPoint.z])
        temp = int(len(self.points)) - 2
        self.lines.append([temp, temp + 1])
        # 水平等高线
        polyData = tvtk.PolyData(points=self.points, lines=self.lines)
        polyDataMapper = tvtk.PolyDataMapper()
        polyDataMapper.set_input_data(polyData)
        actor_contour = tvtk.Actor(mapper=polyDataMapper)
        actor_contour.property.color = (1, 0, 0)
        actor_contour.property.line_width = 2.0
        # 立体等高线
        polyData_ = tvtk.PolyData(points=self.points_, lines=self.lines)
        polyDataMapper_ = tvtk.PolyDataMapper()
        polyDataMapper_.set_input_data(polyData_)
        actor_contour_ = tvtk.Actor(mapper=polyDataMapper_)
        actor_contour_.property.color = (0, 1, 0)
        actor_contour_.property.line_width = 2.0
        return actor_contour, actor_contour_

    def create_struct(self, x, y, z):
        '''
        网格插值主函数（注意区分原始数据与网格数据！！！）
        :param x: 原始数据归一化后的x坐标列表
        :param y: 原始数据归一化后的y坐标列表
        :param z: 原始数据归一化后的z坐标列表
        :return: 输出的X,Y,Z为row*col大小的二维数组，分别代表网格中对应位置点的x,y,z坐标
        '''
        X = np.zeros((self.row + 1, self.col + 1))
        Y = np.zeros((self.row + 1, self.col + 1))
        Z = np.zeros((self.row + 1, self.col + 1))
        count = 0
        for j in range(0, self.col + 1):
            for i in range(0, self.row + 1):
                X[i][j] = x[count]
                Y[i][j] = y[count]
                Z[i][j] = z[count]
                count = count + 1
        return X, Y, Z

    def create_rectangle_list(self, X, Y, Z):
        """
        创建二维数据列表
        :param X:x坐标二维矩阵
        :param Y:y坐标二维矩阵
        :param Z:z坐标二维矩阵
        :return:二维四边形网格列表和一维四边形网格列表
        """
        rectangle_list = []
        rectangles = []
        # 按照行递增列递增的顺序
        for i in range(0, self.row):
            temp = []
            for j in range(0, self.col):
                # 逆时针顺序
                p1 = Point(X[i][j], Y[i][j], Z[i][j])
                p2 = Point(X[i + 1][j], Y[i + 1][j], Z[i + 1][j])
                p3 = Point(X[i + 1][j + 1], Y[i + 1][j + 1], Z[i + 1][j + 1])
                p4 = Point(X[i][j + 1], Y[i][j + 1], Z[i][j + 1])
                rectangle = Rectangle(p1, p2, p3, p4, i, j)
                rectangle.i = i
                rectangle.j = j
                temp.append(rectangle)
                rectangles.append(rectangle)
            rectangle_list.append(temp)
        return rectangle_list, rectangles

    def point_inline(self, p1, p2, z):
        '''
        根据p1,p2的z值和等值线的高度，按比例在p1,p2之间插入一等值线端点p
        :param p1: Point类型（自定义数据类型，详见DataStructure_contour.py）
        :param p2: Point类型（自定义数据类型，详见DataStructure_contour.py）
        :param z: 某一级等值线的高度值
        :return: 返回插入的点p,p也为Point类型
        '''
        x1 = p1.x
        y1 = p1.y
        z1 = p1.z

        x2 = p2.x
        y2 = p2.y
        z2 = p2.z

        zp = z
        ratio = (zp - z1) / (z2 - z1)
        xp = x1 - ratio * (x1 - x2)
        yp = y1 - ratio * (y1 - y2)
        p = Point(xp, yp, zp)
        return p

    def flag_init(self):
        '''
        确定contour_value后对self.flag进行初始化;
        对四边形列表与所有等高线的高程值进行遍历，如果该四边形和该等高面相交则flag标记为1，否则标记为0;
        这一步可以去掉，但是提前将不与等高面相交的四边形标记为已经访问可以有效降低运算时间.
        :return:
        '''

        self.flag = []
        m = len(self.contour_value)  # 等高线条数
        for z in range(m):
            temp = []
            for n in range(len(self.rectangles)):
                rectangle = self.rectangles[n]
                bool_1 = rectangle.p1.z > self.contour_value[z] and rectangle.p2.z > self.contour_value[z] and \
                         rectangle.p3.z > self.contour_value[z] and rectangle.p4.z > self.contour_value[z]
                bool_2 = rectangle.p1.z <= self.contour_value[z] and rectangle.p2.z <= self.contour_value[z] and \
                         rectangle.p3.z <= self.contour_value[z] and rectangle.p4.z <= self.contour_value[z]
                if bool_1 or bool_2:
                    temp.append(0)
                else:
                    temp.append(1)
            self.flag.append(temp)

    def next_Index(self, point, contour_value_cur, rectangle_cur):
        '''
        根据插入的点坐标求下一访问网格序号
        :param point: 等高线段端点
        :param contour_value_cur: 当前高程
        :param rectangle_cur: 当前四边形网格序号
        :return: next_index 下一个访问的四边形网格序号
        '''

        rectangle = self.rectangles[rectangle_cur]
        p1 = rectangle.p1
        p2 = rectangle.p2
        p3 = rectangle.p3
        p4 = rectangle.p4
        cur = contour_value_cur
        # 点在line1上
        if point.y == p1.y:
            i = rectangle.i
            j = rectangle.j - 1
            next_index = i * self.col + j
            if 0 <= i < self.row and 0 <= j < self.col:
                if self.flag[cur][next_index] != 0:
                    return next_index
                else:
                    return -2
            else:
                return -2
        # 点在line3上
        elif point.y == p4.y:
            i = rectangle.i
            j = rectangle.j + 1
            next_index = i * self.col + j
            if 0 <= i < self.row and 0 <= j < self.col:
                if self.flag[cur][next_index] != 0:
                    return next_index
                else:
                    return -2
            else:
                return -2
        # 点在line4上
        elif point.x == p1.x:
            i = rectangle.i - 1
            j = rectangle.j
            next_index = i * self.col + j
            if 0 <= i < self.row and 0 <= j < self.col:
                if self.flag[cur][next_index] != 0:
                    return next_index
                else:
                    return -2
            else:
                return -2
        # 点在line2上
        elif point.x == p2.x:
            i = rectangle.i + 1
            j = rectangle.j
            next_index = i * self.col + j
            if 0 <= i < self.row and 0 <= j < self.col:
                if self.flag[cur][next_index] != 0:
                    return next_index
                else:
                    return -2
            else:
                return -2
        # 不可能
        else:
            pass

    def judge_Rectangle(self, contour_value_cur, rectangle_cur):
        '''
        判断当前访问的网格属于哪种类型，确定两个下次访问的四边形网格序号
        :param contour_value_cur: 高程值序号
        :param rectangle_cur: 当前四边形序号
        :return:
        '''
        z = self.contour_value[contour_value_cur]  # 当前高程值
        rectangle = self.rectangles[rectangle_cur]  # 当前访问的四边形网格
        pre_rectangle = self.rectangles[self.rectangle_cur_last]  # 上一个访问的四边形网格
        # 当前访问的四边形网格行列数
        i = rectangle.i
        j = rectangle.j
        # 上一个访问的四边形网格的行列数
        pre_i = pre_rectangle.i
        pre_j = pre_rectangle.j
        # 当前访问的四边形网格顶点坐标
        p1 = rectangle.p1
        p2 = rectangle.p2
        p3 = rectangle.p3
        p4 = rectangle.p4
        # 0000 or 1111 不可能出现
        if (p1.z > z and p2.z > z and p3.z > z and p4.z > z) or (p1.z <= z and p2.z <= z and p3.z <= z and p4.z <= z):
            pass
        # 0001 or 1110
        elif (p1.z <= z and p2.z <= z and p3.z <= z and p4.z > z) or (p1.z > z and p2.z > z and p3.z > z and p4.z <= z):
            pointa = self.point_inline(p3, p4, z)
            pointb = self.point_inline(p1, p4, z)
            nextIndex1 = self.next_Index(pointa, contour_value_cur, rectangle_cur)
            nextIndex2 = self.next_Index(pointb, contour_value_cur, rectangle_cur)
            line = Edge(pointa, pointb)
            self.flag[contour_value_cur][rectangle_cur] = 0
            return line, nextIndex1, nextIndex2
        # 0010 or 1101
        elif (p1.z <= z and p2.z <= z and p3.z > z and p4.z <= z) or (p1.z > z and p2.z > z and p3.z <= z and p4.z > z):
            pointa = self.point_inline(p2, p3, z)
            pointb = self.point_inline(p3, p4, z)
            nextIndex1 = self.next_Index(pointa, contour_value_cur, rectangle_cur)
            nextIndex2 = self.next_Index(pointb, contour_value_cur, rectangle_cur)
            line = Edge(pointa, pointb)
            self.flag[contour_value_cur][rectangle_cur] = 0
            return line, nextIndex1, nextIndex2
        # 0011 or 1100
        elif (p1.z <= z and p2.z <= z and p3.z > z and p4.z > z) or (p1.z > z and p2.z > z and p3.z <= z and p4.z <= z):
            pointa = self.point_inline(p1, p4, z)
            pointb = self.point_inline(p2, p3, z)
            nextIndex1 = self.next_Index(pointa, contour_value_cur, rectangle_cur)
            nextIndex2 = self.next_Index(pointb, contour_value_cur, rectangle_cur)
            line = Edge(pointa, pointb)
            self.flag[contour_value_cur][rectangle_cur] = 0
            return line, nextIndex1, nextIndex2
        # 0100 or 1011
        elif (p1.z <= z and p2.z > z and p3.z <= z and p4.z <= z) or (p1.z > z and p2.z <= z and p3.z > z and p4.z > z):
            pointa = self.point_inline(p1, p2, z)
            pointb = self.point_inline(p2, p3, z)
            nextIndex1 = self.next_Index(pointa, contour_value_cur, rectangle_cur)
            nextIndex2 = self.next_Index(pointb, contour_value_cur, rectangle_cur)
            line = Edge(pointa, pointb)
            self.flag[contour_value_cur][rectangle_cur] = 0
            return line, nextIndex1, nextIndex2
        # 0101
        elif p1.z <= z and p2.z > z and p3.z <= z and p4.z > z:
            pointa = self.point_inline(p1, p2, z)
            pointb = self.point_inline(p1, p4, z)
            pointc = self.point_inline(p2, p3, z)
            pointd = self.point_inline(p3, p4, z)
            next1 = self.next_Index(pointa, contour_value_cur, rectangle_cur)
            next2 = self.next_Index(pointc, contour_value_cur, rectangle_cur)
            next3 = self.next_Index(pointd, contour_value_cur, rectangle_cur)
            next4 = self.next_Index(pointb, contour_value_cur, rectangle_cur)
            # 第一次遍历该网格
            if self.flag[contour_value_cur][rectangle_cur] == 1:
                if pre_i == i:
                    # 从左边进入
                    if pre_j == j - 1:
                        nextIndex1 = next1
                        nextIndex2 = next4
                        line = Edge(pointa, pointb)
                        self.flag[contour_value_cur][rectangle_cur] = 2  # 表示第一次访问左上角的边
                        return line, nextIndex1, nextIndex2
                    # 从右边进入
                    elif pre_j == j + 1:
                        nextIndex1 = next3
                        nextIndex2 = next4
                        line = Edge(pointd, pointc)
                        self.flag[contour_value_cur][rectangle_cur] = 3  # 表示第一次访问右下角的边
                        return line, nextIndex1, nextIndex2
                    else:  # pre_j = j 第一个四边形网格就是0101，那么就选左上角的线段进行遍历
                        nextIndex1 = next1
                        nextIndex2 = next4
                        line = Edge(pointa, pointb)
                        self.flag[contour_value_cur][rectangle_cur] = 2
                        return line, nextIndex1, nextIndex2
                elif pre_j == j:
                    # 从上面进入
                    if pre_i == i - 1:
                        nextIndex1 = next4
                        nextIndex2 = next1
                        line = Edge(pointb, pointa)
                        self.flag[contour_value_cur][rectangle_cur] = 2
                        return line, nextIndex1, nextIndex2
                    elif pre_i == i + 1:
                        nextIndex1 = next2
                        nextIndex2 = next4
                        line = Edge(pointc, pointd)
                        self.flag[contour_value_cur][rectangle_cur] = 3
                        return line, nextIndex1, nextIndex2
                    else:  # pre_i = i 第一个四边形网格就是0101，那么就选左上角的线段进行遍历
                        nextIndex1 = next1
                        nextIndex2 = next4
                        line = Edge(pointa, pointb)
                        self.flag[contour_value_cur][rectangle_cur] = 2
                        return line, nextIndex1, nextIndex2
                else:
                    pass
            # 第二次遍历该网格且先遍历左上角的边
            elif self.flag[contour_value_cur][rectangle_cur] == 2:
                # 直接返回右下角的边
                nextIndex1 = next2
                nextIndex2 = next3
                line = Edge(pointc, pointd)
                return line, nextIndex1, nextIndex2
            # 第二次遍历该网格且先遍历右下角的边
            elif self.flag[contour_value_cur][rectangle_cur] == 3:
                # 直接返回左上角的边
                nextIndex1 = next1
                nextIndex2 = next4
                line = Edge(pointa, pointb)
                return line, nextIndex1, nextIndex2
            else:  # 不可能出现
                pass
        # 1010
        elif p1.z > z and p2.z <= z and p3.z > z and p4.z <= z:
            pointa = self.point_inline(p1, p2, z)
            pointb = self.point_inline(p2, p3, z)
            pointc = self.point_inline(p3, p4, z)
            pointd = self.point_inline(p1, p4, z)
            next1 = self.next_Index(pointa, contour_value_cur, rectangle_cur)
            next2 = self.next_Index(pointb, contour_value_cur, rectangle_cur)
            next3 = self.next_Index(pointc, contour_value_cur, rectangle_cur)
            next4 = self.next_Index(pointd, contour_value_cur, rectangle_cur)
            # 第一次遍历该网格
            if self.flag[contour_value_cur][rectangle_cur] == 1:
                if pre_i == i:
                    # 从左边进入
                    if pre_j == j - 1:
                        nextIndex1 = next1
                        nextIndex2 = next2
                        line = Edge(pointa, pointb)
                        self.flag[contour_value_cur][rectangle_cur] = 4  # 表示第一次访问左下角的边
                        return line, nextIndex1, nextIndex2
                    # 从右边进入
                    elif pre_j == j + 1:
                        nextIndex1 = next3
                        nextIndex2 = next4
                        line = Edge(pointc, pointd)
                        self.flag[contour_value_cur][rectangle_cur] = 5  # 表示第一次访问右上角的边
                        return line, nextIndex1, nextIndex2
                    else:  # pre_j = j 第一个四边形网格就是1010，那么就选左下角的线段进行遍历
                        nextIndex1 = next1
                        nextIndex2 = next2
                        line = Edge(pointa, pointb)
                        self.flag[contour_value_cur][rectangle_cur] = 4
                        return line, nextIndex1, nextIndex2
                elif pre_j == j:
                    # 从上面进入
                    if pre_i == i - 1:
                        nextIndex1 = next4
                        nextIndex2 = next3
                        line = Edge(pointd, pointc)
                        self.flag[contour_value_cur][rectangle_cur] = 5  # 表示第一次访问右上角的边
                        return line, nextIndex1, nextIndex2
                    # 从下面进入
                    elif pre_i == i + 1:
                        nextIndex1 = next1
                        nextIndex2 = next2
                        line = Edge(pointb, pointa)
                        self.flag[contour_value_cur][rectangle_cur] = 4  # 表示第一次访问左下角的边
                        return line, nextIndex1, nextIndex2
                    else:  # pre_i = i 第一个四边形网格就是1010，那么就选左下角的线段进行遍历
                        nextIndex1 = next1
                        nextIndex2 = next2
                        line = Edge(pointa, pointb)
                        self.flag[contour_value_cur][rectangle_cur] = 4
                        return line, nextIndex1, nextIndex2
                else:
                    pass
            # 第二次遍历该网格且先遍历左下角的边
            elif self.flag[contour_value_cur][rectangle_cur] == 4:
                # 直接返回右上角的边
                nextIndex1 = next2
                nextIndex2 = next3
                line = Edge(pointc, pointd)
                # 将标记置零
                self.flag[contour_value_cur][rectangle_cur] = 0
                return line, nextIndex1, nextIndex2
            # 第二次遍历该网格且先遍历右上角的边
            elif self.flag[contour_value_cur][rectangle_cur] == 5:
                # 直接返回左下角的边
                nextIndex1 = next1
                nextIndex2 = next2
                line = Edge(pointa, pointb)
                # 将标记置零
                self.flag[contour_value_cur][rectangle_cur] = 0
                return line, nextIndex1, nextIndex2
            else:  # 不可能出现
                pass
        # 0110 or 1001
        elif (p1.z <= z and p2.z > z and p3.z > z and p4.z <= z) or (p1.z > z and p2.z <= z and p3.z <= z and p4.z > z):
            pointa = self.point_inline(p1, p2, z)
            pointb = self.point_inline(p3, p4, z)
            nextIndex1 = self.next_Index(pointa, contour_value_cur, rectangle_cur)
            nextIndex2 = self.next_Index(pointb, contour_value_cur, rectangle_cur)
            line = Edge(pointa, pointb)
            self.flag[contour_value_cur][rectangle_cur] = 0
            return line, nextIndex1, nextIndex2
        # 0111 or 1000
        elif (p1.z <= z and p2.z > z and p3.z > z and p4.z > z) or (p1.z > z and p2.z <= z and p3.z <= z and p4.z <= z):
            pointa = self.point_inline(p1, p2, z)
            pointb = self.point_inline(p1, p4, z)
            nextIndex1 = self.next_Index(pointa, contour_value_cur, rectangle_cur)
            nextIndex2 = self.next_Index(pointb, contour_value_cur, rectangle_cur)
            line = Edge(pointa, pointb)
            self.flag[contour_value_cur][rectangle_cur] = 0
            return line, nextIndex1, nextIndex2
        else:  # 不可能
            pass

    def find_next_lineSlot(self):
        '''
        每隔一段时间自动追踪下一条等高线段
        '''
        new_line = None  # 初始化新创建的等高线线段
        label = 0  # 如果可以在循环结束之前找到新的等高线线段则label被置为1且立即跳出循环
        while self.contour_value_cur < len(self.contour_value):
            # 这里self.contour_value_cur在下一次进入该函数仍会接着上一次执行位置的下一步来开始
            while self.rectangle_cur < len(self.rectangles):
                # self.rectangle_cur表示当前访问的网格序号，更改后也会保存
                rectangle = self.rectangles[self.rectangle_cur]
                i = rectangle.i
                j = rectangle.j
                # flag = 1
                # 进入有线段还没有被遍历过的网格
                if self.flag[self.contour_value_cur][self.rectangle_cur] == 1:
                    # 下面这一句传回该网格包围的等高线线段 line, 以及两个相邻网格索引(不存在就返回None)
                    new_line, nextIndex1, nextIndex2 = self.judge_Rectangle(self.contour_value_cur, self.rectangle_cur)
                    if nextIndex1 == -2:
                        if nextIndex2 == -2:
                            # 此处表示访问到这条等高线的一个尽头
                            if self.leafIndex != -1 and self.flag[self.contour_value_cur][self.leafIndex] != 0:
                                self.rectangle_cur_last = self.rectangle_cur
                                self.rectangle_cur = self.leafIndex  # 如果这条等高线还有一部分没有被访问就去访问 leaf
                                self.leafIndex = -1  # -1只是表示他已经被用过一次了，下一次不要再用 leaf
                            else:
                                self.baseIndex += 1  # 这条等高线已经追踪完毕，马上去找下一条
                                self.rectangle_cur_last = self.rectangle_cur
                                self.rectangle_cur = self.baseIndex
                        else:
                            self.rectangle_cur_last = self.rectangle_cur
                            self.rectangle_cur = nextIndex2  # 单向行驶，没有顾虑
                    else:
                        if nextIndex2 == -2:
                            self.rectangle_cur_last = self.rectangle_cur
                            self.rectangle_cur = nextIndex1  # 单向行驶，没有顾虑
                        else:
                            self.leafIndex = nextIndex1
                            self.rectangle_cur_last = self.rectangle_cur  # 访问到一条新的等高线的"腰部"
                            self.rectangle_cur = nextIndex2  # 先随便找一个方向去追踪，追踪完了再去另一头 leaf

                    label = 1  # 在循环结束之前找到新的等高线线段，那么就标志一下
                    break  # 跳出第一层循环
                # 四种特殊情况
                elif self.flag[self.contour_value_cur][self.rectangle_cur] > 1:
                    # 下面这一句传回该网格包围的等高线线段 line, 以及两个相邻网格索引(不存在就返回None)
                    new_line, nextIndex1, nextIndex2 = self.judge_Rectangle(self.contour_value_cur, self.rectangle_cur)
                    self.flag[self.contour_value_cur][self.rectangle_cur] = 0  # 下次不要访问我了
                    if nextIndex1 == -2:
                        if nextIndex2 == -2:
                            # 此处表示访问到这条等高线的一个尽头
                            if self.leafIndex != -1 and self.flag[self.contour_value_cur][self.leafIndex] != 0:
                                self.rectangle_cur_last = self.rectangle_cur
                                self.rectangle_cur = self.leafIndex  # 如果这条等高线还有一部分没有被访问就去访问 leaf
                                self.leafIndex = -1  # -1只是表示他已经被用过一次了，下一次不要再用 leaf
                            else:
                                self.baseIndex += 1  # 这条等高线已经追踪完毕，马上去找下一条
                                self.rectangle_cur_last = self.rectangle_cur
                                self.rectangle_cur = self.baseIndex
                        else:
                            self.rectangle_cur_last = self.rectangle_cur
                            self.rectangle_cur = nextIndex2  # 单向行驶，没有顾虑
                    else:
                        if nextIndex2 == -2:
                            self.rectangle_cur_last = self.rectangle_cur
                            self.rectangle_cur = nextIndex1  # 单向行驶，没有顾虑
                        else:
                            self.rectangle_cur_last = self.rectangle_cur
                            self.leafIndex = nextIndex1  # 访问到一条新的等高线的"腰部"
                            self.rectangle_cur = nextIndex2  # 先随便找一个方向去追踪，追踪完了再去另一头 leaf

                    label = 1  # 在循环结束之前找到新的等高线线段，那么就标志一下
                    break  # 跳出第一层循环
                else:  # 该四边形网格内部没有等高线段，去找下一条等高线
                    self.baseIndex += 1
                    self.rectangle_cur_last = self.rectangle_cur
                    self.rectangle_cur = self.baseIndex
            if label == 0:  # 代表这一层楼(等高面)已经被全部访问了，接下来更上一层楼
                self.contour_value_cur += 1  # 上楼之前把参数恢复到初始状态
                self.baseIndex = 0
                self.leafIndex = -1
                self.rectangle_cur_last = 0
                self.rectangle_cur = 0
            else:  # label == 1
                break  # 在循环结束之前找到新的等高线线段，跳出第二层循环

        if label == 0:
            pass  # 没有等高线线段可以被找到
        else:  # label ==1 有一条新的等高线线段生成，接下来对等高线实体进行更新
            if "actor_contour" in dir(self):
                self.viewer.scene.remove_actor(self.actor_contour)  # 如果原来有平面等高线实体就移除
                self.viewer.scene.remove_actor(self.actor_contour_)  # 如果原来有立体等高线实体就移除
                del self.actor_contour  # 删除self.actor_contour
                del self.actor_contour_  # 删除self.actor_contour_
            else:
                pass
            # update_actor_contour函数是自定义的，表示更新等高线实体
            self.actor_contour, self.actor_contour_ = self.update_actor_contour(new_line)
            self.viewer.scene.add_actor(self.actor_contour)  # 重新添加平面等高线实体
            self.viewer.scene.add_actor(self.actor_contour_)  # 重新添加立体等高线实体

        self.viewer.scene.render()  # 刷新界面(没有生成新的线段也可以刷新)

    def getContour(self, contour_num, custom_contour):
        # 等高线设置弹框点击确认之后_signal被发送到此处
        # 根据重新设置后的等高线重新对等高线进行设置
        self.viewer.scene.remove_actor(self.actor_grid)
        self.viewer.scene.remove_actor(self.actor_contour)
        self.viewer.scene.remove_actor(self.actor_contour_)
        del self.actor_grid
        del self.actor_contour
        del self.actor_contour_
        self.plot_surface()
        self.contour_num = contour_num
        self.custom_contour = custom_contour
        self.contour_value = np.append(
            np.linspace((self.z.max() - self.z.min()) / (self.contour_num + 1), self.z.max(), self.contour_num,
                        endpoint=False), np.array(self.custom_contour))
        self.flag_init()
        self.points = []
        self.points_ = []
        self.lines = []
        self.contour_value_cur = 0
        self.baseIndex = 0
        self.leafIndex = -1
        self.rectangle_cur = 0
        self.timer.start(20)
