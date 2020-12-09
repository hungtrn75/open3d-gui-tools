#!/usr/bin/env python3
import glob
import numpy as np
import open3d as o3d
import open3d.visualization.gui as gui
import open3d.visualization.rendering as rendering
import os
import platform
import sys
from pyntcloud import PyntCloud
import pylas

isMacOS = platform.system() == "Darwin"


class Settings:
    UNLIT = "defaultUnlit"
    LIT = "defaultLit"
    NORMALS = "normals"
    DEPTH = "depth"

    DEFAULT_PROFILE_NAME = "Bright day with sun at +Y [default]"
    POINT_CLOUD_PROFILE_NAME = "Cloudy day (no direct sun)"
    CUSTOM_PROFILE_NAME = "Custom"
    LIGHTING_PROFILES = {
        DEFAULT_PROFILE_NAME: {
            "ibl_intensity": 45000,
            "sun_intensity": 45000,
            "sun_dir": [0.577, -0.577, -0.577],
            # "ibl_rotation":
            "use_ibl": True,
            "use_sun": True,
        },
        "Bright day with sun at -Y": {
            "ibl_intensity": 45000,
            "sun_intensity": 45000,
            "sun_dir": [0.577, 0.577, 0.577],
            # "ibl_rotation":
            "use_ibl": True,
            "use_sun": True,
        },
        "Bright day with sun at +Z": {
            "ibl_intensity": 45000,
            "sun_intensity": 45000,
            "sun_dir": [0.577, 0.577, -0.577],
            # "ibl_rotation":
            "use_ibl": True,
            "use_sun": True,
        },
        "Less Bright day with sun at +Y": {
            "ibl_intensity": 35000,
            "sun_intensity": 50000,
            "sun_dir": [0.577, -0.577, -0.577],
            # "ibl_rotation":
            "use_ibl": True,
            "use_sun": True,
        },
        "Less Bright day with sun at -Y": {
            "ibl_intensity": 35000,
            "sun_intensity": 50000,
            "sun_dir": [0.577, 0.577, 0.577],
            # "ibl_rotation":
            "use_ibl": True,
            "use_sun": True,
        },
        "Less Bright day with sun at +Z": {
            "ibl_intensity": 35000,
            "sun_intensity": 50000,
            "sun_dir": [0.577, 0.577, -0.577],
            # "ibl_rotation":
            "use_ibl": True,
            "use_sun": True,
        },
        POINT_CLOUD_PROFILE_NAME: {
            "ibl_intensity": 60000,
            "sun_intensity": 50000,
            "use_ibl": True,
            "use_sun": False,
            # "ibl_rotation":
        },
    }

    DEFAULT_MATERIAL_NAME = "Polished ceramic [default]"
    PREFAB = {
        DEFAULT_MATERIAL_NAME: {
            "metallic": 0.0,
            "roughness": 0.7,
            "reflectance": 0.5,
            "clearcoat": 0.2,
            "clearcoat_roughness": 0.2,
            "anisotropy": 0.0,
        },
        "Metal (rougher)": {
            "metallic": 1.0,
            "roughness": 0.5,
            "reflectance": 0.9,
            "clearcoat": 0.0,
            "clearcoat_roughness": 0.0,
            "anisotropy": 0.0,
        },
        "Metal (smoother)": {
            "metallic": 1.0,
            "roughness": 0.3,
            "reflectance": 0.9,
            "clearcoat": 0.0,
            "clearcoat_roughness": 0.0,
            "anisotropy": 0.0,
        },
        "Plastic": {
            "metallic": 0.0,
            "roughness": 0.5,
            "reflectance": 0.5,
            "clearcoat": 0.5,
            "clearcoat_roughness": 0.2,
            "anisotropy": 0.0,
        },
        "Glazed ceramic": {
            "metallic": 0.0,
            "roughness": 0.5,
            "reflectance": 0.9,
            "clearcoat": 1.0,
            "clearcoat_roughness": 0.1,
            "anisotropy": 0.0,
        },
        "Clay": {
            "metallic": 0.0,
            "roughness": 1.0,
            "reflectance": 0.5,
            "clearcoat": 0.1,
            "clearcoat_roughness": 0.287,
            "anisotropy": 0.0,
        },
    }

    def __init__(self):
        self.mouse_model = gui.SceneWidget.Controls.ROTATE_CAMERA
        self.bg_color = gui.Color(1, 1, 1)
        self.show_skybox = False
        self.show_axes = False
        self.use_ibl = True
        self.use_sun = True
        self.new_ibl_name = None  # clear to None after loading
        self.ibl_intensity = 45000
        self.sun_intensity = 45000
        self.sun_dir = [0.577, -0.577, -0.577]
        self.sun_color = gui.Color(1, 1, 1)

        self.apply_material = False  # clear to False after processing
        self._materials = {
            Settings.LIT: rendering.Material(),
            Settings.UNLIT: rendering.Material(),
            Settings.NORMALS: rendering.Material(),
            Settings.DEPTH: rendering.Material(),
        }
        self._materials[Settings.LIT].base_color = [0.9, 0.9, 0.9, 1.0]
        self._materials[Settings.LIT].shader = Settings.LIT
        self._materials[Settings.UNLIT].base_color = [0.9, 0.9, 0.9, 1.0]
        self._materials[Settings.UNLIT].shader = Settings.UNLIT
        self._materials[Settings.NORMALS].shader = Settings.NORMALS
        self._materials[Settings.DEPTH].shader = Settings.DEPTH

        self.material = self._materials[Settings.LIT]

    def set_material(self, name):
        self.material = self._materials[name]

    def apply_material_prefab(self, name):
        assert self.material.shader == Settings.LIT
        prefab = Settings.PREFAB[name]
        for key, val in prefab.items():
            setattr(self.material, "base_" + key, val)

    def apply_lighting_profile(self, name):
        profile = Settings.LIGHTING_PROFILES[name]
        for key, val in profile.items():
            setattr(self, key, val)


class AppWindow:
    MENU_OPEN = 1
    MENU_DOWNSAMPLING = 4
    MENU_EXPORT = 2
    MENU_EXPORT_LAS = 5
    MENU_QUIT = 3
    MENU_SHOW_SETTINGS = 11
    MENU_ABOUT = 21
    MENU_CLOSE_ALL = 6
    MENU_CROP_GEOMETRY = 7

    DEFAULT_IBL = "default"

    MATERIAL_NAMES = ["Lit", "Unlit", "Normals", "Depth"]
    MATERIAL_SHADERS = [Settings.LIT, Settings.UNLIT, Settings.NORMALS, Settings.DEPTH]
    # Config values
    _checkeds = [True, True, True, True]
    _geometry = None
    _d_geometry = None
    _c_geometry = None
    _s_geometry = None
    _downsampling = 0.0
    _path = None
    _infile = None

    def __init__(self, width, height):
        self.settings = Settings()
        resource_path = gui.Application.instance.resource_path
        self.settings.new_ibl_name = resource_path + "/" + AppWindow.DEFAULT_IBL

        self.window = gui.Application.instance.create_window("Open3D", width, height)
        w = self.window  # to make the code more concise

        # 3D widget
        self._scene = gui.SceneWidget()
        self._scene.scene = rendering.Open3DScene(w.renderer)
        self._scene.set_on_sun_direction_changed(self._on_sun_dir)

        em = w.theme.font_size

        separation_height = int(round(0.5 * em))
        self._settings_panel = gui.Vert(
            0, gui.Margins(0.25 * em, 0.25 * em, 0.25 * em, 0.25 * em)
        )

        db_ctrls = gui.CollapsableVert("DB Tree", 0.25 * em, gui.Margins(em, 0, 0, 0))

        main_layout = gui.Horiz()
        crop_layout = gui.Horiz()
        downsample_layout = gui.Horiz()
        sub_layout = gui.Horiz()
        self._fileedit_2 = gui.Checkbox("source")
        self._fileedit_3 = gui.Checkbox("cropped")
        self._fileedit_4 = gui.Checkbox("downsample")
        self._fileedit_5 = gui.Checkbox("sub")
        self._fileedit_2.checked = True
        self._fileedit_3.checked = True
        self._fileedit_4.checked = True
        self._fileedit_5.checked = True

        self._fileedit_2.set_on_checked(self._on_db_main_checked)
        self._fileedit_3.set_on_checked(self._on_db_crop_checked)
        self._fileedit_4.set_on_checked(self._on_db_downsample_checked)
        self._fileedit_5.set_on_checked(self._on_db_sub_checked)

        self._fileedit_main = gui.Label("(NoData)")

        self._fileedit_crop = gui.Label("(NoData)")
        self._fileedit_downsample = gui.Label("(NoData)")
        self._fileedit_sub = gui.Label("(NoData)")

        main_layout.add_child(self._fileedit_2)
        main_layout.add_fixed(0.25 * em)
        main_layout.add_child(self._fileedit_main)

        downsample_layout.add_child(self._fileedit_4)
        downsample_layout.add_fixed(0.25 * em)
        downsample_layout.add_child(self._fileedit_downsample)

        crop_layout.add_child(self._fileedit_3)
        crop_layout.add_fixed(0.25 * em)
        crop_layout.add_child(self._fileedit_crop)

        sub_layout.add_child(self._fileedit_5)
        sub_layout.add_fixed(0.25 * em)
        sub_layout.add_child(self._fileedit_sub)

        self._fileedit = gui.TextEdit()
        filedlgbutton = gui.Button("...")
        filedlgbutton.horizontal_padding_em = 0.5
        filedlgbutton.vertical_padding_em = 0
        filedlgbutton.set_on_clicked(self._on_filedlg_button)
        fileedit_layout = gui.Horiz()
        fileedit_layout.add_child(gui.Label("Choose crop file"))
        fileedit_layout.add_child(self._fileedit)
        fileedit_layout.add_fixed(0.25 * em)
        fileedit_layout.add_child(filedlgbutton)

        db_ctrls.add_child(main_layout)
        db_ctrls.add_child(downsample_layout)
        db_ctrls.add_child(crop_layout)
        db_ctrls.add_child(sub_layout)
        db_ctrls.add_fixed(0.1 * em)
        db_ctrls.add_child(fileedit_layout)

        self._settings_panel.add_child(db_ctrls)

        view_ctrls = gui.CollapsableVert(
            "View controls", 0.25 * em, gui.Margins(em, 0, 0, 0)
        )

        self._arcball_button = gui.Button("Arcball")
        self._arcball_button.horizontal_padding_em = 0.5
        self._arcball_button.vertical_padding_em = 0
        self._arcball_button.set_on_clicked(self._set_mouse_mode_rotate)
        self._fly_button = gui.Button("Fly")
        self._fly_button.horizontal_padding_em = 0.5
        self._fly_button.vertical_padding_em = 0
        self._fly_button.set_on_clicked(self._set_mouse_mode_fly)
        self._model_button = gui.Button("Model")
        self._model_button.horizontal_padding_em = 0.5
        self._model_button.vertical_padding_em = 0
        self._model_button.set_on_clicked(self._set_mouse_mode_model)
        self._sun_button = gui.Button("Sun")
        self._sun_button.horizontal_padding_em = 0.5
        self._sun_button.vertical_padding_em = 0
        self._sun_button.set_on_clicked(self._set_mouse_mode_sun)
        self._ibl_button = gui.Button("Environment")
        self._ibl_button.horizontal_padding_em = 0.5
        self._ibl_button.vertical_padding_em = 0
        self._ibl_button.set_on_clicked(self._set_mouse_mode_ibl)
        view_ctrls.add_child(gui.Label("Mouse controls"))

        h = gui.Horiz(0.25 * em)  # row 1
        h.add_stretch()
        h.add_child(self._arcball_button)
        h.add_child(self._fly_button)
        h.add_child(self._model_button)
        h.add_stretch()
        view_ctrls.add_child(h)
        h = gui.Horiz(0.25 * em)  # row 2
        h.add_stretch()
        h.add_child(self._sun_button)
        h.add_child(self._ibl_button)
        h.add_stretch()
        view_ctrls.add_child(h)

        self._show_skybox = gui.Checkbox("Show skymap")
        self._show_skybox.set_on_checked(self._on_show_skybox)
        view_ctrls.add_fixed(separation_height)
        view_ctrls.add_child(self._show_skybox)

        self._bg_color = gui.ColorEdit()
        self._bg_color.set_on_value_changed(self._on_bg_color)

        grid = gui.VGrid(2, 0.25 * em)
        grid.add_child(gui.Label("BG Color"))
        grid.add_child(self._bg_color)
        view_ctrls.add_child(grid)

        self._show_axes = gui.Checkbox("Show axes")
        self._show_axes.set_on_checked(self._on_show_axes)
        view_ctrls.add_fixed(separation_height)
        view_ctrls.add_child(self._show_axes)

        self._profiles = gui.Combobox()
        for name in sorted(Settings.LIGHTING_PROFILES.keys()):
            self._profiles.add_item(name)
        self._profiles.add_item(Settings.CUSTOM_PROFILE_NAME)
        self._profiles.set_on_selection_changed(self._on_lighting_profile)
        view_ctrls.add_fixed(separation_height)
        view_ctrls.add_child(gui.Label("Lighting profiles"))
        view_ctrls.add_child(self._profiles)
        self._settings_panel.add_fixed(separation_height)
        self._settings_panel.add_child(view_ctrls)

        advanced = gui.CollapsableVert("Advanced lighting", 0, gui.Margins(em, 0, 0, 0))
        advanced.set_is_open(False)

        self._use_ibl = gui.Checkbox("HDR map")
        self._use_ibl.set_on_checked(self._on_use_ibl)
        self._use_sun = gui.Checkbox("Sun")
        self._use_sun.set_on_checked(self._on_use_sun)
        advanced.add_child(gui.Label("Light sources"))
        h = gui.Horiz(em)
        h.add_child(self._use_ibl)
        h.add_child(self._use_sun)
        advanced.add_child(h)

        self._ibl_map = gui.Combobox()
        for ibl in glob.glob(gui.Application.instance.resource_path + "/*_ibl.ktx"):

            self._ibl_map.add_item(os.path.basename(ibl[:-8]))
        self._ibl_map.selected_text = AppWindow.DEFAULT_IBL
        self._ibl_map.set_on_selection_changed(self._on_new_ibl)
        self._ibl_intensity = gui.Slider(gui.Slider.INT)
        self._ibl_intensity.set_limits(0, 200000)
        self._ibl_intensity.set_on_value_changed(self._on_ibl_intensity)
        grid = gui.VGrid(2, 0.25 * em)
        grid.add_child(gui.Label("HDR map"))
        grid.add_child(self._ibl_map)
        grid.add_child(gui.Label("Intensity"))
        grid.add_child(self._ibl_intensity)
        advanced.add_fixed(separation_height)
        advanced.add_child(gui.Label("Environment"))
        advanced.add_child(grid)

        self._sun_intensity = gui.Slider(gui.Slider.INT)
        self._sun_intensity.set_limits(0, 200000)
        self._sun_intensity.set_on_value_changed(self._on_sun_intensity)
        self._sun_dir = gui.VectorEdit()
        self._sun_dir.set_on_value_changed(self._on_sun_dir)
        self._sun_color = gui.ColorEdit()
        self._sun_color.set_on_value_changed(self._on_sun_color)
        grid = gui.VGrid(2, 0.25 * em)
        grid.add_child(gui.Label("Intensity"))
        grid.add_child(self._sun_intensity)
        grid.add_child(gui.Label("Direction"))
        grid.add_child(self._sun_dir)
        grid.add_child(gui.Label("Color"))
        grid.add_child(self._sun_color)
        advanced.add_fixed(separation_height)
        advanced.add_child(gui.Label("Sun (Directional light)"))
        advanced.add_child(grid)

        self._settings_panel.add_fixed(separation_height)
        self._settings_panel.add_child(advanced)

        material_settings = gui.CollapsableVert(
            "Material settings", 0, gui.Margins(em, 0, 0, 0)
        )

        # material_settings.set_is_open(False)

        self._shader = gui.Combobox()
        self._shader.add_item(AppWindow.MATERIAL_NAMES[0])
        self._shader.add_item(AppWindow.MATERIAL_NAMES[1])
        self._shader.add_item(AppWindow.MATERIAL_NAMES[2])
        self._shader.add_item(AppWindow.MATERIAL_NAMES[3])
        # self._shader.set_on_selection_changed(self._on_shader)
        self._material_prefab = gui.Combobox()
        for prefab_name in sorted(Settings.PREFAB.keys()):
            self._material_prefab.add_item(prefab_name)
        self._material_prefab.selected_text = Settings.DEFAULT_MATERIAL_NAME
        self._material_prefab.set_on_selection_changed(self._on_material_prefab)
        self._material_color = gui.ColorEdit()
        self._material_color.set_on_value_changed(self._on_material_color)
        self._point_size = gui.Slider(gui.Slider.INT)
        self._point_size.set_limits(1, 10)
        self._point_size.set_on_value_changed(self._on_point_size)

        grid = gui.VGrid(2, 0.25 * em)
        grid.add_child(gui.Label("Type"))
        grid.add_child(self._shader)
        grid.add_child(gui.Label("Material"))
        grid.add_child(self._material_prefab)
        grid.add_child(gui.Label("Color"))
        grid.add_child(self._material_color)
        grid.add_child(gui.Label("Point size"))
        grid.add_child(self._point_size)
        material_settings.add_child(grid)

        self._settings_panel.add_fixed(separation_height)
        self._settings_panel.add_child(material_settings)

        w.set_on_layout(self._on_layout)
        w.add_child(self._scene)
        w.add_child(self._settings_panel)

        if gui.Application.instance.menubar is None:
            if isMacOS:
                app_menu = gui.Menu()
                app_menu.add_item("About", AppWindow.MENU_ABOUT)
                app_menu.add_separator()
                app_menu.add_item("Quit", AppWindow.MENU_QUIT)
            file_menu = gui.Menu()
            file_menu.add_item("Open...", AppWindow.MENU_OPEN)
            file_menu.add_separator()
            file_menu.add_item("Downsamle PointCloud", AppWindow.MENU_DOWNSAMPLING)
            file_menu.add_item("Crop Geometry", AppWindow.MENU_CROP_GEOMETRY)
            file_menu.add_separator()
            file_menu.add_item("Export Current Image...", AppWindow.MENU_EXPORT)
            file_menu.add_item("Export to .las file", AppWindow.MENU_EXPORT_LAS)
            file_menu.add_separator()
            file_menu.add_item("Clear all", AppWindow.MENU_CLOSE_ALL)
            if not isMacOS:
                file_menu.add_separator()
                file_menu.add_item("Quit", AppWindow.MENU_QUIT)
            settings_menu = gui.Menu()
            settings_menu.add_item("Lighting & Materials", AppWindow.MENU_SHOW_SETTINGS)
            settings_menu.set_checked(AppWindow.MENU_SHOW_SETTINGS, True)
            help_menu = gui.Menu()
            help_menu.add_item("About", AppWindow.MENU_ABOUT)

            menu = gui.Menu()
            if isMacOS:
                menu.add_menu("Example", app_menu)
                menu.add_menu("File", file_menu)
                menu.add_menu("Settings", settings_menu)
            else:
                menu.add_menu("File", file_menu)
                menu.add_menu("Settings", settings_menu)
                menu.add_menu("Help", help_menu)
            gui.Application.instance.menubar = menu

        w.set_on_menu_item_activated(AppWindow.MENU_OPEN, self._on_menu_open)
        w.set_on_menu_item_activated(
            AppWindow.MENU_DOWNSAMPLING, self._on_menu_downsampling
        )
        w.set_on_menu_item_activated(AppWindow.MENU_EXPORT, self._on_menu_export)
        w.set_on_menu_item_activated(
            AppWindow.MENU_EXPORT_LAS, self._on_menu_export_las
        )
        w.set_on_menu_item_activated(AppWindow.MENU_QUIT, self._on_menu_quit)
        w.set_on_menu_item_activated(AppWindow.MENU_CLOSE_ALL, self._on_menu_close_all)
        w.set_on_menu_item_activated(
            AppWindow.MENU_SHOW_SETTINGS, self._on_menu_toggle_settings_panel
        )
        w.set_on_menu_item_activated(AppWindow.MENU_ABOUT, self._on_menu_about)
        w.set_on_menu_item_activated(
            AppWindow.MENU_CROP_GEOMETRY, self._on_menu_crop_geometry
        )
        # ----

        self._apply_settings()

    def _apply_settings(self):
        bg_color = [
            self.settings.bg_color.red,
            self.settings.bg_color.green,
            self.settings.bg_color.blue,
            self.settings.bg_color.alpha,
        ]
        self._scene.scene.set_background_color(bg_color)
        self._scene.scene.show_skybox(self.settings.show_skybox)
        self._scene.scene.show_axes(self.settings.show_axes)
        if self.settings.new_ibl_name is not None:
            self._scene.scene.scene.set_indirect_light(self.settings.new_ibl_name)
            self.settings.new_ibl_name = None
        self._scene.scene.scene.enable_indirect_light(self.settings.use_ibl)
        self._scene.scene.scene.set_indirect_light_intensity(
            self.settings.ibl_intensity
        )
        sun_color = [
            self.settings.sun_color.red,
            self.settings.sun_color.green,
            self.settings.sun_color.blue,
        ]
        self._scene.scene.scene.set_directional_light(
            self.settings.sun_dir, sun_color, self.settings.sun_intensity
        )
        self._scene.scene.scene.enable_directional_light(self.settings.use_sun)

        if self.settings.apply_material:
            self._scene.scene.update_material(self.settings.material)
            self.settings.apply_material = False

        self._bg_color.color_value = self.settings.bg_color
        self._show_skybox.checked = self.settings.show_skybox
        self._show_axes.checked = self.settings.show_axes
        self._use_ibl.checked = self.settings.use_ibl
        self._use_sun.checked = self.settings.use_sun
        self._ibl_intensity.int_value = self.settings.ibl_intensity
        self._sun_intensity.int_value = self.settings.sun_intensity
        self._sun_dir.vector_value = self.settings.sun_dir
        self._sun_color.color_value = self.settings.sun_color
        self._material_prefab.enabled = self.settings.material.shader == Settings.LIT
        c = gui.Color(
            self.settings.material.base_color[0],
            self.settings.material.base_color[1],
            self.settings.material.base_color[2],
            self.settings.material.base_color[3],
        )
        self._material_color.color_value = c
        self._point_size.double_value = self.settings.material.point_size

    def _on_layout(self, theme):
        r = self.window.content_rect
        width = 20 * theme.font_size
        self._scene.frame = gui.Rect(width, 0, r.width - width, r.height)
        self._settings_panel.frame = gui.Rect(0, 0, width, r.height)

    def _on_db_main_checked(self, state):
        self._checkeds[0] = state
        if self._geometry is not None:
            self._scene.scene.show_geometry("__model__", state)
            self._scene.scene.show_geometry("__m_bounds__", state)
        print(state)

    def _on_db_downsample_checked(self, state):
        self._checkeds[1] = state
        if self._d_geometry is not None:
            self._scene.scene.show_geometry("__downsample__", state)
            self._scene.scene.show_geometry("__d_bounds__", state)
        print(state)

    def _on_db_sub_checked(self, state):
        self._checkeds[3] = state
        if self._s_geometry is not None:
            self._scene.scene.show_geometry("__sub__", state)
            self._scene.scene.show_geometry("__s_bounds__", state)

    def _on_db_crop_checked(self, state):
        self._checkeds[2] = state
        if self._c_geometry is not None:
            self._scene.scene.show_geometry("__cropped__", state)
            self._scene.scene.show_geometry("__c_bounds__", state)

    def _on_filedlg_button(self):
        filedlg = gui.FileDialog(gui.FileDialog.OPEN, "Select file", self.window.theme)
        filedlg.add_filter(".ply", "Poind Cloud(.ply)")
        filedlg.set_on_cancel(self._on_filedlg_cancel)
        filedlg.set_on_done(self._on_filedlg_done)
        self.window.show_dialog(filedlg)

    def _on_filedlg_cancel(self):
        self.window.close_dialog()

    def _on_filedlg_done(self, path):
        self._fileedit.text_value = path
        pcd = None
        if self._d_geometry is None:
            pcd = self._geometry
        else:
            pcd = self._d_geometry
        if pcd is not None:
            c_pcd = o3d.io.read_point_cloud(path)
            dists = pcd.compute_point_cloud_distance(c_pcd)
            dists = np.asarray(dists)
            ind = np.where(dists > 0.01)[0]
            pcd_without_cropped = pcd.select_by_index(ind)
            # Add cropped geo to scene
            self._scene.scene.add_geometry("__cropped__", c_pcd, self.settings.material)
            self._fileedit_sub.text = "({0} points)".format(len(c_pcd.points))
            c_bounds = c_pcd.get_axis_aligned_bounding_box()
            c_bounds.color = (1, 0, 0)
            self._scene.scene.add_geometry("__c_bounds__", c_bounds, self.settings.material)
            # Add sub geo to scene
            self._scene.scene.add_geometry(
                "__sub__", pcd_without_cropped, self.settings.material
            )
            self._fileedit_sub.text = "({0} points)".format(len(pcd_without_cropped.points))
            s_bounds = pcd_without_cropped.get_axis_aligned_bounding_box()
            s_bounds.color = (1, 0, 0)
            self._scene.scene.add_geometry("__s_bounds__", s_bounds, self.settings.material)
            self._c_geometry = c_pcd
            self._fileedit_crop.text = "({0} points)".format(len(c_pcd.points))
            self._s_geometry = pcd_without_cropped
            self._fileedit_sub.text = "({0} points)".format(len(pcd_without_cropped.points))

        self.window.close_dialog()

        
    def _set_mouse_mode_rotate(self):
        self._scene.set_view_controls(gui.SceneWidget.Controls.ROTATE_CAMERA)

    def _set_mouse_mode_fly(self):
        self._scene.set_view_controls(gui.SceneWidget.Controls.FLY)

    def _set_mouse_mode_model(self):
        self._scene.set_view_controls(gui.SceneWidget.Controls.ROTATE_MODEL)

    def _set_mouse_mode_sun(self):
        self._scene.set_view_controls(gui.SceneWidget.Controls.ROTATE_SUN)

    def _set_mouse_mode_ibl(self):
        self._scene.set_view_controls(gui.SceneWidget.Controls.ROTATE_IBL)

    def _on_bg_color(self, new_color):
        self.settings.bg_color = new_color
        self._apply_settings()

    def _on_show_skybox(self, show):
        self.settings.show_skybox = show
        self._apply_settings()

    def _on_show_axes(self, show):
        self.settings.show_axes = show
        self._apply_settings()

    def _on_use_ibl(self, use):
        self.settings.use_ibl = use
        self._profiles.selected_text = Settings.CUSTOM_PROFILE_NAME
        self._apply_settings()

    def _on_use_sun(self, use):
        self.settings.use_sun = use
        self._profiles.selected_text = Settings.CUSTOM_PROFILE_NAME
        self._apply_settings()

    def _on_lighting_profile(self, name, index):
        if name != Settings.CUSTOM_PROFILE_NAME:
            self.settings.apply_lighting_profile(name)
            self._apply_settings()

    def _on_new_ibl(self, name, index):
        self.settings.new_ibl_name = gui.Application.instance.resource_path + "/" + name
        self._profiles.selected_text = Settings.CUSTOM_PROFILE_NAME
        self._apply_settings()

    def _on_ibl_intensity(self, intensity):
        self.settings.ibl_intensity = int(intensity)
        self._profiles.selected_text = Settings.CUSTOM_PROFILE_NAME
        self._apply_settings()

    def _on_sun_intensity(self, intensity):
        self.settings.sun_intensity = int(intensity)
        self._profiles.selected_text = Settings.CUSTOM_PROFILE_NAME
        self._apply_settings()

    def _on_sun_dir(self, sun_dir):
        self.settings.sun_dir = sun_dir
        self._profiles.selected_text = Settings.CUSTOM_PROFILE_NAME
        self._apply_settings()

    def _on_sun_color(self, color):
        self.settings.sun_color = color
        self._apply_settings()

    def _on_shader(self, name, index):
        self.settings.set_material(AppWindow.MATERIAL_SHADERS[index])
        self._apply_settings()

    def _on_material_prefab(self, name, index):
        self.settings.apply_material_prefab(name)
        self.settings.apply_material = True
        self._apply_settings()

    def _on_material_color(self, color):
        self.settings.material.base_color = [
            color.red,
            color.green,
            color.blue,
            color.alpha,
        ]
        self.settings.apply_material = True
        self._apply_settings()

    def _on_point_size(self, size):
        self.settings.material.point_size = int(size)
        self.settings.apply_material = True
        self._apply_settings()

    def _on_menu_open(self):
        dlg = gui.FileDialog(
            gui.FileDialog.OPEN, "Choose file to load", self.window.theme
        )

        dlg.add_filter(".las", "LAS files (.las)")

        dlg.set_on_cancel(self._on_file_dialog_cancel)
        dlg.set_on_done(self._on_load_dialog_done)
        self.window.show_dialog(dlg)

    def _on_file_dialog_cancel(self):
        self.window.close_dialog()

    def _on_load_dialog_done(self, filename):
        self.window.close_dialog()
        self._on_menu_close_all()
        self.load(filename)

    def _on_menu_close_all(self):
        self.window.title = "Open3D"
        self._scene.scene.clear_geometry()
        self._fileedit_main.text = ""
        self._fileedit_downsample.text = ""
        self._fileedit_crop.text = ""
        self._fileedit_sub.text = ""
        self._geometry = None
        self._d_geometry = None
        self._c_geometry = None
        self._s_geometry = None
        self._checkeds = [True, True, True, True]
        self._fileedit_2.checked = True
        self._fileedit_3.checked = True
        self._fileedit_4.checked = True
        self._fileedit_5.checked = True
        self._infile = None

    def _on_menu_crop_geometry(self):
        if self._geometry is not None or self._d_geometry is not None:
            c_geometry = None
            if self._d_geometry is None:
                c_geometry = self._geometry
            else:
                c_geometry = self._d_geometry

            if c_geometry is not None:
                o3d.visualization.draw_geometries_with_editing(
                    [c_geometry], "CropWindowOpen3D"
                )

    def _on_menu_export_las(self):
        len_true = np.sum(self._checkeds)
        if len_true != 1:
            self.window.show_message_box("Warning", "Chi chon mot geometry de export!")
        else:
            if (
                self._geometry is not None
                or self._d_geometry is not None
                or self._c_geometry is not None
                or self._s_geometry is not None
            ):
                dlg = gui.FileDialog(
                    gui.FileDialog.SAVE, "Choose file to save", self.window.theme
                )
                dlg.add_filter(".las", "LAS files (.las)")
                dlg.set_on_cancel(self._on_file_dialog_cancel)
                dlg.set_on_done(self._on_export_las_dialog_done)
                self.window.show_dialog(dlg)

    def _on_menu_export(self):
        dlg = gui.FileDialog(
            gui.FileDialog.SAVE, "Choose file to save", self.window.theme
        )
        dlg.add_filter(".png", "PNG files (.png)")
        dlg.set_on_cancel(self._on_file_dialog_cancel)
        dlg.set_on_done(self._on_export_dialog_done)
        self.window.show_dialog(dlg)

    def _on_export_las_dialog_done(self, filename):
        self.window.close_dialog()
        e_geometry = None
        if self._checkeds[0]:
            e_geometry = self._geometry
        elif self._checkeds[1]:
            e_geometry = self._d_geometry
        elif self._checkeds[2]:
            e_geometry = self._c_geometry
        else:
            e_geometry = self._s_geometry

        las = pylas.create(point_format_id=self._infile.point_format.id)
        las.header = self._infile.header
        scales = self._infile.header.scales
        pcd_points = np.asarray(e_geometry.points)
        len_shape = len(pcd_points)
        reshape_points = np.reshape(pcd_points.T, (3, len_shape))
        las.__setitem__("X", reshape_points[0] / scales[0])
        las.__setitem__("Y", reshape_points[1] / scales[1])
        las.__setitem__("Z", reshape_points[2] / scales[2])

        if e_geometry.has_colors():
            pcd_colors = np.asarray(e_geometry.colors)
            reshape_colors = np.reshape(pcd_colors.T, (3, len_shape))
            las.__setattr__("red", reshape_colors[0] * 65536)
            las.__setattr__("green", reshape_colors[1] * 65536)
            las.__setattr__("blue", reshape_colors[2] * 65536)

        las.write(filename)
        self._on_export_las_success(filename)

    def _on_export_las_success(self, filename):
        em = self.window.theme.font_size
        dlg = gui.Dialog("Export file")
        dlg_layout = gui.Vert(em, gui.Margins(em, em, em, em))
        dlg_layout.add_child(gui.Label("Saved to " + filename))
        ok = gui.Button("OK")
        ok.set_on_clicked(self._on_cancel_downsamling)
        dlg_layout.add_child(ok)
        dlg.add_child(dlg_layout)
        self.window.show_dialog(dlg)

    def _on_export_dialog_done(self, filename):
        self.window.close_dialog()
        frame = self._scene.frame
        self.export_image(filename, frame.width, frame.height)

    def _on_menu_quit(self):
        gui.Application.instance.quit()

    def _on_menu_toggle_settings_panel(self):
        self._settings_panel.visible = not self._settings_panel.visible
        gui.Application.instance.menubar.set_checked(
            AppWindow.MENU_SHOW_SETTINGS, self._settings_panel.visible
        )

    def _on_menu_downsampling(self):
        em = self.window.theme.font_size
        dlg = gui.Dialog("Downsampling")
        dlg_layout = gui.Vert(em, gui.Margins(em, em, em, em))
        dlg_layout.add_child(gui.Label("Cloud sub Sampling"))

        h = gui.Horiz()
        h.add_child(gui.Label("Min. space between points"))
        doubleedit = gui.NumberEdit(gui.NumberEdit.DOUBLE)
        doubleedit.set_limits(0.0, 10.0)
        if self._downsampling is not None:
            doubleedit.set_value(self._downsampling)
        doubleedit.set_on_value_changed(self._on_doubleedit_value_change)
        h.add_child(doubleedit)

        ok = gui.Button("OK")
        ok.set_on_clicked(self._on_aply_downsamling)
        cancel = gui.Button("Cancel")
        cancel.set_on_clicked(self._on_cancel_downsamling)

        dlg_layout.add_child(h)
        h2 = gui.Horiz()
        h2.add_stretch()
        h2.add_child(cancel)
        h2.add_fixed(em)
        h2.add_child(ok)
        dlg_layout.add_child(h2)

        dlg.add_child(dlg_layout)
        self.window.show_dialog(dlg)

    def _on_cancel_downsamling(self):
        self.window.close_dialog()

    def _on_aply_downsamling(self):
        self.window.close_dialog()
        if self._geometry is not None:
            if self._downsampling == 0.0:
                self._d_geometry = None
                self._fileedit_downsample.text = ""
                self._scene.scene.remove_geometry("__downsample__")
                self._scene.scene.remove_geometry("__d_bounds__")
                self._scene.scene.add_geometry(
                    "__model__", self._geometry, self.settings.material
                )
            else:
                self._scene.scene.remove_geometry("__downsample__")

                self._d_geometry = self._geometry.voxel_down_sample(
                    voxel_size=self._downsampling
                )
                bounds = self._d_geometry.get_axis_aligned_bounding_box()
                bounds.color = (1, 0, 0)
                oriented = self._d_geometry.get_oriented_bounding_box()
                oriented.color = (0, 1, 0)
                self._scene.scene.add_geometry(
                    "__d_bounds__", bounds, self.settings.material
                )

                self._fileedit_downsample.text = "({0} points)".format(
                    len(self._d_geometry.points)
                )
                self._scene.scene.add_geometry(
                    "__downsample__", self._d_geometry, self.settings.material
                )

    def _on_doubleedit_value_change(self, value):
        print(value)
        self._downsampling = value

    def _on_menu_about(self):
        em = self.window.theme.font_size
        dlg = gui.Dialog("About")

        dlg_layout = gui.Vert(em, gui.Margins(em, em, em, em))
        dlg_layout.add_child(gui.Label("Open3D GUI Example"))

        ok = gui.Button("OK")
        ok.set_on_clicked(self._on_about_ok)

        h = gui.Horiz()
        h.add_stretch()
        h.add_child(ok)
        h.add_stretch()
        dlg_layout.add_child(h)

        dlg.add_child(dlg_layout)
        self.window.show_dialog(dlg)

    def _on_about_ok(self):
        self.window.close_dialog()

    def _load_gui_on_main_thread(self):
        print("Run on main start......")
        if self._geometry is not None:
            try:
                self._scene.scene.add_geometry(
                    "__model__", self._geometry, self.settings.material
                )
                self._fileedit_main.text = "({0} points)".format(
                    len(self._geometry.points)
                )
                bounds = self._geometry.get_axis_aligned_bounding_box()
                bounds.color = (1, 0, 0)
                self._scene.scene.add_geometry(
                    "__m_bounds__", bounds, self.settings.material
                )

                self._scene.setup_camera(60, bounds, bounds.get_center())

                print("Run on main done......")

            except Exception as e:
                print(e)
        self.window.close_dialog()

    def _load_gui_on_separate_thread(self):
        if self._geometry is None:
            cloud = None
            try:
                pynt_cloud = PyntCloud.from_file(self._path)
                self._infile = pylas.read(self._path)
                cloud = pynt_cloud.to_instance("open3d", mesh=False)
                if cloud.has_colors():
                    r_colors = np.asarray(cloud.colors)
                    cloud.colors = o3d.utility.Vector3dVector(r_colors / 255)
            except Exception:
                pass
            if cloud is not None:
                print("[Info] Successfully read", self._path)
                if not cloud.has_normals():
                    cloud.estimate_normals()
                cloud.normalize_normals()
                self._geometry = cloud
                print(np.asarray(cloud.colors))
            else:
                print("[WARNING] Failed to read points", self.path)
            print("Run on separate done......")
            gui.Application.instance.post_to_main_thread(
                self.window, self._load_gui_on_main_thread
            )

    def _show_cropping_dialog(self):
        em = self.window.theme.font_size
        dlg = gui.Dialog("Processing data")
        dlg_layout = gui.Vert(em, gui.Margins(em, em, em, em))
        dlg_layout.add_child(gui.Label("Cropping geometry..."))
        dlg.add_child(dlg_layout)
        self.window.show_dialog(dlg)

    def _show_processing_dialog(self):
        em = self.window.theme.font_size
        dlg = gui.Dialog("Processing data")
        dlg_layout = gui.Vert(em, gui.Margins(em, em, em, em))
        dlg_layout.add_child(gui.Label("normalize the normals of point cloud"))
        dlg.add_child(dlg_layout)
        self.window.show_dialog(dlg)

    def load(self, path):
        self._path = path
        self.window.title = path
        self._show_processing_dialog()
        gui.Application.instance.run_in_thread(self._load_gui_on_separate_thread)

    def export_image(self, path, width, height):
        def on_image(image):
            img = image

            quality = 9  # png
            if path.endswith(".jpg"):
                quality = 100
            o3d.io.write_image(path, img, quality)

        self._scene.scene.scene.render_to_image(on_image)


def main():
    # We need to initalize the application, which finds the necessary shaders
    # for rendering and prepares the cross-platform window abstraction.
    gui.Application.instance.initialize()

    w = AppWindow(1920, 1080)

    if len(sys.argv) > 1:
        path = sys.argv[1]
        if os.path.exists(path):
            w.load(path)
        else:
            w.window.show_message_box("Error", "Could not open file '" + path + "'")

    # Run the event loop. This will not return until the last window is closed.
    gui.Application.instance.run()


if __name__ == "__main__":
    main()
