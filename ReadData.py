import numpy as np

def readPoints(filename):
    # 读取散点数据
    x = []
    y = []
    z = []

    with open(filename, "r") as f:
        while True:
            lines = f.readline()
            if not lines:
                break
                pass
            x_tmp, y_tmp, z_tmp = [float(i) for i in lines.split()]
            x.append(x_tmp)
            y.append(y_tmp)
            z.append(z_tmp)
            pass
        x = np.array(x)
        y = np.array(y)
        z = np.array(z)

    length = len(x)

    data = np.zeros((length, 3))
    for i in range(length):
        data[i][0] = x[i]
        data[i][1] = y[i]
        data[i][2] = z[i]
    # 归一化
    x = (x - x.min()) / (x.max() - x.min())
    y = (y - y.min()) / (y.max() - y.min())
    z = (z - z.min()) / (z.max() - z.min())
    return x, y, z, data  # data是一个矩阵，访问方式为data[i][j]
