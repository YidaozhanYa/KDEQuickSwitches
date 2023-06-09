from switches.interfaces import BaseSwitch
from dataclasses import dataclass
from PyQt5.QtCore import QSettings
import PyQt5.QtDBus as QDBus
from gi.repository import Gio
import os
import glob
import subprocess as sp


@dataclass
class DarkModeConfig:
    LIGHT_KVANTUM_THEME = "Fluent-round"  # Light Kvantum theme
    DARK_KVANTUM_THEME = "Fluent-roundDark"  # Dark Kvantum theme

    LIGHT_GTK_THEME = "Fluent-round-Light"  # Light GTK2/3 theme
    DARK_GTK_THEME = "Fluent-round-Dark"  # Dark GTK2/3 theme

    LIGHT_GTK4_THEME = "Fluent-round-Light"  # Light GTK4 theme
    DARK_GTK4_THEME = "Fluent-round-Dark"  # Dark GTK4 theme

    LIGHT_COLOR_SCHEME = "FluentLight"  # Light color scheme
    DARK_COLOR_SCHEME = "FluentDark"  # Dark color scheme

    LIGHT_ICON_THEME = "Win10Sur"  # Light icon theme
    DARK_ICON_THEME = "Win10Sur-dark"  # Dark icon theme

    LIGHT_FCITX5_THEME = "微软拼音"  # Light fcitx5 skin
    DARK_FCITX5_THEME = "plasma"  # Dark fcitx5 skin

    LIGHT_WALLPAPER = "file:$HOME/.local/share/Steam/steamapps/workshop/content/431960/2239430876/原神风景-wallpaper.mp4+video".replace(
        "$HOME", os.environ.get("HOME")
    )  # Light wallpaper source
    LIGHT_WALLPAPER_ID = "2239430876"

    DARK_WALLPAPER = "file:$HOME/.local/share/Steam/steamapps/workshop/content/431960/2375520960/scene.json+scene".replace(
        "$HOME", os.environ.get("HOME")
    )  # Dark wallpaper source
    DARK_WALLPAPER_ID = "2375520960"


class DarkModeSwitch(BaseSwitch):
    def __init__(self):
        super().__init__(
            name="夜间模式",
            icon="weather-clear-night",
            icon_disabled="weather-clear",
        )
        self.config = DarkModeConfig()
        self.kvantum_config = QSettings(
            os.path.join(
                os.environ.get("XDG_CONFIG_HOME"),
                "Kvantum",
                "kvantum.kvconfig",
            ),
            QSettings.IniFormat,
        )
        self.kvantum_config.setIniCodec("UTF-8")
        self.gnome_config = Gio.Settings.new("org.gnome.desktop.interface")
        self.fcitx5_ui_config_path = os.path.join(
            os.environ.get("XDG_CONFIG_HOME"),
            "fcitx5",
            "conf",
            "classicui.conf",
        )
        self.state = self.get()
        print(f"Dark mode is {self.state}.")

    def set_wallpaper(self, source: str, id: str):
        script = """
                var allDesktops = desktops();
        for (i=0;i<allDesktops.length;i++) {
            d = allDesktops[i];
            d.wallpaperPlugin = "com.github.casout.wallpaperEngineKde";
            d.currentConfigGroup = Array("Wallpaper",
                                        "com.github.casout.wallpaperEngineKde",
                                        "General");
            d.writeConfig("WallpaperSource", "SOURCE");
            d.writeConfig("WallpaperWorkShopId", "ID");
        }
        """.replace(
            "SOURCE", source
        ).replace(
            "ID", id
        )
        msg = QDBus.QDBusMessage.createMethodCall(
            "org.kde.plasmashell",
            "/PlasmaShell",
            "org.kde.PlasmaShell",
            "evaluateScript",
        )
        msg.setArguments([script])
        QDBus.QDBusConnection.sessionBus().call(msg)

    def get(self) -> bool:
        current_kvantum_theme = self.kvantum_config.value("theme")
        if current_kvantum_theme == self.config.LIGHT_KVANTUM_THEME:
            return False
        elif current_kvantum_theme == self.config.DARK_KVANTUM_THEME:
            return True
        else:
            return False

    def set(self, value: bool):
        self.state = value
        # 删除之前的 GTK4 主题
        for f in glob.glob(
            os.path.join(
                os.environ.get("XDG_CONFIG_HOME"),
                "gtk-4.0",
                "*.css",
            )
        ):
            os.remove(f)
        # 设置壁纸
        self.set_wallpaper(
            self.config.DARK_WALLPAPER
            if value
            else self.config.LIGHT_WALLPAPER,
            self.config.DARK_WALLPAPER_ID
            if value
            else self.config.LIGHT_WALLPAPER_ID,
        )
        # 设置颜色主题
        sp.run(
            [
                "plasma-apply-colorscheme",
                (
                    self.config.DARK_COLOR_SCHEME
                    if value
                    else self.config.LIGHT_COLOR_SCHEME
                ),
            ]
        )
        # 设置图标主题
        sp.run(
            [
                "/usr/lib/plasma-changeicons",
                (
                    self.config.DARK_ICON_THEME
                    if value
                    else self.config.LIGHT_ICON_THEME
                ),
            ]
        )
        # 设置 GTK 主题
        self.gnome_config.set_string(
            "gtk-theme",
            self.config.DARK_GTK_THEME
            if value
            else self.config.LIGHT_GTK_THEME,
        )
        # 设置 GNOME 应用程序主题为深色
        self.gnome_config.set_string(
            "color-scheme",
            "prefer-dark" if value else "prefer-light",
        )
        # 设置 kvantum 主题
        sp.run(
            [
                "kvantummanager",
                "--set",
                self.config.DARK_KVANTUM_THEME
                if value
                else self.config.LIGHT_KVANTUM_THEME,
            ]
        )
        # 设置 fcitx5 主题
        fcitx5_ui_config = open(self.fcitx5_ui_config_path, "r").readlines()
        for i in range(len(fcitx5_ui_config)):
            if fcitx5_ui_config[i].startswith("Theme="):
                fcitx5_ui_config[i] = (
                    "Theme="
                    + (
                        self.config.DARK_FCITX5_THEME
                        if value
                        else self.config.LIGHT_FCITX5_THEME
                    )
                    + "\n"
                )
                break
        with open(self.fcitx5_ui_config_path, "w") as f:
            f.writelines(fcitx5_ui_config)
        # 加载 GTK4 主题
        sp.run(
            [
                "cp",
                "-r",
                os.path.join(
                    os.environ.get("HOME"),
                    ".themes",
                    self.config.DARK_GTK4_THEME
                    if value
                    else self.config.LIGHT_GTK4_THEME,
                    "gtk-4.0",
                ),
                os.environ.get("XDG_CONFIG_HOME"),
            ]
        )
        # 重新加载 Qt 控件主题
        STYlE_CHANGED = 2
        SETTINGS_STYLE = 7
        msg = QDBus.QDBusMessage.createSignal(
            "/KGlobalSettings", "org.kde.KGlobalSettings", "notifyChange"
        )
        msg.setArguments({STYlE_CHANGED, SETTINGS_STYLE})
        QDBus.QDBusConnection.sessionBus().send(msg)
        # 重新加载KWin
        msg = QDBus.QDBusMessage.createMethodCall(
            "org.kde.KWin",
            "/KWin",
            "org.kde.KWin",
            "reconfigure",
        )
        QDBus.QDBusConnection.sessionBus().call(msg)
        # 重新加载 fcitx5
        msg = QDBus.QDBusMessage.createMethodCall(
            "org.fcitx.Fcitx5",
            "/controller",
            "org.fcitx.Fcitx.Controller1",
            "ReloadAddonConfig",
        )
        msg.setArguments(["classicui"])
        QDBus.QDBusConnection.sessionBus().call(msg)

        color = "40" if value else "242"
        self.ref_window.setStyleSheet(
            """
            #mainWindow {
                background: rgb(COLOR, COLOR, COLOR);
                margin: 0px;
                padding: 0px;
            }
        """.replace(
                "COLOR", color
            )
        )
        print(f"Set dark mode to {self.state}.")
