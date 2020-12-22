import argparse
import open3d as o3d
import pathlib
import os

if __name__ == "__main__":
    dir_path = pathlib.Path().absolute()
    tmp = os.path.join(dir_path,"tmp.pcd")
    pcd  = o3d.io.read_point_cloud(tmp)
    vis = o3d.visualization.VisualizerWithEditing(-1.0, False, "")
    vis.create_window()
    vis.add_geometry(pcd)
    vis.run() 
    vis.destroy_window()
    geo = vis.get_cropped_geometry()
    w_path = os.path.join(dir_path,"c_geo.pcd")
    o3d.io.write_point_cloud( w_path, geo)

