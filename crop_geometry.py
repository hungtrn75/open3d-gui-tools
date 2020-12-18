import argparse
import open3d as o3d

if __name__ == "__main__":
    tmp = r"C:\Users\SkyMap\Desktop\open3d\open3d-gui-tools-main\tmp\tmp.pcd"
    pcd  = o3d.io.read_point_cloud(tmp)
    vis = o3d.visualization.VisualizerWithEditing(-1.0, False, "")
    vis.create_window()
    vis.add_geometry(pcd)
    vis.run() 
    vis.destroy_window()
    geo = vis.get_cropped_geometry()
    w_path = r"C:\Users\SkyMap\Desktop\open3d\open3d-gui-tools-main\tmp\c_geo.pcd"
    o3d.io.write_point_cloud( w_path, geo)

