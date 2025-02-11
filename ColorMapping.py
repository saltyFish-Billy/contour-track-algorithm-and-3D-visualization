def ColorMapping(m_colors):
    '''
    根据设定的控制点个数完成对长度为256的色表的插值
    :param m_colors: 种子点颜色，值形式：[[R,G,B],[R,G,B],...,[R,G,B]]
                     初始默认值为：[[255, 0.0, 255], [0.0, 255, 255],
                     [0.0, 0.0, 255], [0.0, 255, 0.0], [255, 255, 0.0],
                     [255, 125, 0.0], [255, 0.0, 0.0]]
    :return: 返回TVTK色表LookupTable，长度为256
    '''
    LookupTable = []
    total_dis = 0
    count = 0
    # 累加
    dis_add_list = [0.0]
    # 不累加
    dis_list = []
    for i in range(len(m_colors) - 1):
        dis = distance(m_colors[i], m_colors[i + 1])
        total_dis = dis + total_dis
        dis_list.append(dis)
        dis_add_list.append(total_dis)
    # 插值的距离间隔
    insert_dis = total_dis / 255
    # 色表起始颜色
    LookupTable.append((int(m_colors[0][0]), int(m_colors[0][1]), int(m_colors[0][2])))
    # 色表插值
    for i in range(255):
        if (i + 1) * insert_dis > dis_add_list[count + 1]:
            count = count + 1
        near_dis = (i + 1) * insert_dis - dis_add_list[count]
        color = insert_one_color(m_colors[count], m_colors[count + 1], near_dis / dis_list[count])
        LookupTable.append(color)
    return LookupTable


def insert_one_color(color1, color2, D):
    '''
    根据两端点的颜色对其中某一点进行颜色插值（线性插值）
    :param color1: 起始颜色(R,G,B)(0~255)
    :param color2: 终止颜色(R,G,B)(0~255)
    :param D: 插值颜色到起始颜色的距离/终止颜色到起始颜色的距离
    :return: 返回该点插值后的颜色
    '''
    # version1 date 2022/12/7 17:17
    # 计算插值颜色R，G，B值
    R = int(color1[0] - (color1[0] - color2[0]) * D)
    G = int(color1[1] - (color1[1] - color2[1]) * D)
    B = int(color1[2] - (color1[2] - color2[2]) * D)
    i_color = (R, G, B)
    return i_color


def distance(c_point1, c_point2):
    '''
    求两个颜色点之间的几何距离
    :param c_point1: 颜色点，形式（R，G，B）
    :param c_point2: 颜色点，形式（R，G，B）
    :return:
    '''
    dis = ((c_point1[0] - c_point2[0]) ** 2 + (c_point1[1] - c_point2[1]) ** 2 + (
            c_point1[2] - c_point2[2]) ** 2) ** 0.5
    return dis
