# coding: utf-8
import laspy
import CSF
import numpy as np

inFile = laspy.file.File(r"C:\Users\SkyMap\Desktop\open3d\open3d-gui-tools-main\sub_test2.las", mode='r') # read a las file
points = inFile.points

# def csf():
xyz = np.vstack((inFile.x, inFile.y, inFile.z)).transpose() # extract x, y, z and put into a list
print(xyz)
csf = CSF.CSF()

# prameter settings
csf.params.bSloopSmooth = False
csf.params.cloth_resolution = 0.2
# more details about parameter: http://ramm.bnu.edu.cn/projects/CSF/download/
csf.setPointCloud(xyz)
ground = CSF.VecInt()  # a list to indicate the index of ground points after calculation
non_ground = CSF.VecInt() # a list to indicate the index of non-ground points after calculation
csf.do_filtering(ground, non_ground) # do actual filtering.
outFile = laspy.file.File(r"q002.las",
                          mode='w', header=inFile.header)
outFile.points = points[ground] # extract ground points, and save it to a las file.
outFile.close() # do not forget this