import numpy as np
import copy
import open3d as o3d
from pyntcloud import PyntCloud
from laspy.file import File
import pandas as pd
import pylas

def find_first(item,array):
    for i in array:
        result_0 = 1
        result_1 = 1
        result_2 = 1
        if item[0]>i[0]:
            result_0= (item[0] + i[0] // 2) // i[0]
            result_1= (item[1] + i[1] // 2) // i[1]
            result_2= (item[2] + i[2] // 2) // i[2]
        else:
            result_0= (i[0] + item[0] // 2) // item[0]
            result_1= (i[1] + item[1] // 2) // item[1]
            result_2= (i[2] + item[2] // 2) // item[2]
        if (result_1 % 10) ==0 and (result_2 % 10) ==0 and (result_0) % 10 == 0:
            return True 
    return False

def create():
    r_las = pylas.read('/Users/macbook/Downloads/Test1.las')

    cloud = PyntCloud.from_file("/Users/macbook/Downloads/Test1.las")
    pcd = cloud.to_instance("open3d", mesh=False)
    dpcd = pcd
    # dpcd = pcd.voxel_down_sample(voxel_size=0.05)
    pcd_points = np.asarray(dpcd.points)
    print(r_las.header.offsets)
    las = pylas.create(point_format_id=r_las.point_format.id)
    las.header = r_las.header
    scales =  r_las.header.scales
    reshape_points = np.reshape(pcd_points.T,(3,len(pcd_points)))
    print( reshape_points[0])
    las.__setitem__('X',reshape_points[0]/scales[0])
    las.__setitem__('Y',reshape_points[1]/scales[1])
    las.__setitem__('Z',reshape_points[2]/scales[2])
    # las.x = reshape_points[0]
    # las.y = reshape_points[1]
    # las.z = reshape_points[2]
    if pcd.has_colors():
        pcd_colors = np.asarray(dpcd.colors)
        reshape_colors = np.reshape(pcd_colors.T,(3,len(pcd_colors)))
        las.__setattr__("red",reshape_colors[0]*256)
        las.__setattr__("green",reshape_colors[1]*256)
        las.__setattr__("blue",reshape_colors[2]*256)
    print(las.points)
    print(r_las.points)
    las.write('C:/Users/hungt/Downloads/diagonal.las')

def pylas_test():
    t_points = []
    las = pylas.read('C:/Users/hungt/Downloads/points.las')
    cloud = PyntCloud.from_file("C:/Users/hungt/Downloads/points.las")
    pcd = cloud.to_instance("open3d", mesh=False)
    if not pcd.has_normals():
                    pcd.estimate_normals()
    pcd.normalize_normals()
    pcd_points = np.asarray(pcd.points)
    print(pcd_points)
    print(las.points)

def main():
    cloud = PyntCloud.from_file("C:/Users/hungt/Downloads/points.las")
    pcd = cloud.to_instance("open3d", mesh=False)
    inFile = File("C:/Users/hungt/Downloads/points.las", mode = "r")

    points = pd.DataFrame(data=np.asarray(pcd.points),
                              columns=["x", "y", "z"])
                
    if pcd.colors:
        colors = (np.asarray(pcd.colors) * 255).astype(np.uint8)
        points["red"] = colors[:, 0]
        points["green"] = colors[:, 1]
        points["blue"] = colors[:, 2]

    if pcd.normals:
        normals = np.asarray(pcd.normals)
        points["nx"] = normals[:, 0]
        points["ny"] = normals[:, 1]
        points["nz"] = normals[:, 2]
    print(points)
    coords = np.vstack((inFile.x, inFile.y, inFile.z)).transpose()
    first_point = coords[0,:]

    # Calculate the euclidean distance from all points to the first point

    distances = np.sum((coords - first_point)**2, axis = 1)

    # Create an array of indicators for whether or not a point is less than
    # 500000 units away from the first point

    keep_points = distances < 500000

    # Grab an array of all points which meet this threshold

    points_kept = inFile.points[keep_points]
    print(points_kept)

def crop_geo():
    c_pcd = o3d.io.read_point_cloud("C:/Users/hungt/Downloads/cropped_2.ply")
    cloud = PyntCloud.from_file("C:/Users/hungt/Downloads/points.las")
    pcd = cloud.to_instance("open3d", mesh=False)
    pcd_points = np.asarray(pcd.points)
    c_pcd_points = np.asarray(c_pcd.points)
    print(list(pcd_points))
    r_pcd = np.reshape(pcd_points.T,(3,len(pcd_points)))
    r_c_pcd = np.reshape(c_pcd_points.T,(3,len(c_pcd_points)))
    print((r_pcd[0]))
    print(len(r_pcd[1]))
    print(len(r_pcd[2]))
    print((r_c_pcd[0]))
    print(len(r_c_pcd[1]))
    print(len(r_c_pcd[2]))
    r_x_pcd = np.setdiff1d(r_pcd[0],r_c_pcd[0])
    r_y_pcd = np.setdiff1d(r_pcd[1],r_c_pcd[1])
    r_z_pcd = np.setdiff1d(r_pcd[2],r_c_pcd[2])
    print(len(r_x_pcd))
    print(len(r_y_pcd))
    print(len(r_z_pcd))
    # ,c_pcd.get_axis_aligned_bounding_box()
    # rc_pcd = pcd.crop(c_pcd.get_oriented_bounding_box())
    # o3d.visualization.draw_geometries([pcd])

def crop_geo_2():
    c_pcd = o3d.io.read_point_cloud("C:/Users/hungt/Downloads/cropped_1.ply")
    cloud = PyntCloud.from_file("C:/Users/hungt/Downloads/points.las")
    pcd = cloud.to_instance("open3d", mesh=False)
    dists = pcd.compute_point_cloud_distance(c_pcd)
    dists = np.asarray(dists)
    ind = np.where(dists > 0.01)[0]
    pcd_without_cropped = pcd.select_by_index(ind)
    o3d.visualization.draw_geometries([pcd_without_cropped])


def color():
    # pcd = o3d.io.read_point_cloud("/Users/macbook/Desktop/python/open3d-gui-tools/rockyperla.ply")
    # print(np.asarray(pcd.colors))
    cloud = PyntCloud.from_file("/Users/macbook/Downloads/Test1.las")
    t_pcd = cloud.to_instance("open3d", mesh=False)
    r_colors = np.asarray(t_pcd.colors)
    t_pcd.colors = o3d.utility.Vector3dVector(r_colors/255)
    print(np.asarray(t_pcd.colors))

if __name__ == "__main__":
    color()
