from pyntcloud import PyntCloud
import pylas
import open3d as o3d
import numpy as np
from laspy.file import File
import time
print("start")
# path = r"C:\Users\SkyMap\Desktop\Test3.las"
path = r"C:/Users/SkyMap/Desktop/open3d/open3d-gui-tools-main/q002.las"
# x = time.time()
pynt_cloud = PyntCloud.from_file(path)
print(pynt_cloud)
# y = time.time()
# print(pynt_cloud)
# print("0",y-x)
inFile = File(path, mode='r')

# z = time.time()
print(inFile.points)
# print("1",z-y)
cloud = pynt_cloud.to_instance("open3d", mesh=False)
print(cloud)
# t = time.time()
# print("2",t-z)
# a = pylas.read(path)
# k = time.time()
# print("3",k-t)
if cloud.has_colors():
                    r_colors = np.asarray(cloud.colors)
                    cloud.colors = o3d.utility.Vector3dVector(r_colors / 255)
# h = time.time()                    
# print("4", h-k)