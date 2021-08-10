import argparse
import open3d as o3d
import pathlib
import os

if __name__ == "__main__":
    dir_path = pathlib.Path().absolute()
    root_path = str(dir_path).split("\\")
    root_path = (root_path[:-1])
    new_path = "\\"
    new_path = new_path.join(root_path)
    tmp = os.path.join(new_path, r"temp\tmp.pcd")

    pcd  = o3d.io.read_point_cloud(tmp)
    vis = o3d.visualization.VisualizerWithEditing(-1.0, False, "")
    vis.create_window("Lọc thủ công")
    vis.add_geometry(pcd)
    vis.run() 
    vis.destroy_window()
    geo = vis.get_cropped_geometry()
    if len(geo.points) == len(pcd.points):
        print(False)
    else:    
        w_path = os.path.join(new_path, r"temp\c_geo.pcd")
        o3d.io.write_point_cloud( w_path, geo)
        print(True)
    

