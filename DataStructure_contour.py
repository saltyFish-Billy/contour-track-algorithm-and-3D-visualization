# 等值线算法中的数据结构

class Point:
    def __init__(self, x, y, z):
        self.x = x  # X坐标
        self.y = y  # Y坐标
        self.z = z  # Z坐标

    def __eq__(self, other):
        # 重载"=="判断符号
        if (self.x == other.x) and (self.y == other.y):
            return 1
        else:
            return 0


class Edge:
    def __init__(self, p1, p2):
        self.BeginPoint = p1
        self.EndPoint = p2

    def __eq__(self, other):
        # 重载"=="判断符号
        if (self.BeginPoint == other.EndPoint and
                self.EndPoint == other.BeginPoint):
            return 1
        elif (self.BeginPoint == other.BeginPoint and
              self.EndPoint == other.EndPoint):
            return 1
        else:
            return 0


class Rectangle:
    def __init__(self, p1, p2, p3, p4, i, j):
        #矩形网格的四个点，逆时针顺序
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.p4 = p4
        self.i = i
        self.j = j

    def __eq__(self, other):
        if (self.p1 == other.p1 and self.p2 == other.p2 and
                self.p3 == other.p3 and self.p4 == other.p4):
            return 1
        else:
            return 0
