from PySide6.QtCore import Slot, Signal
from PySide6.QtWidgets import QWidget, QListWidgetItem
from data.ui.modpacks import Ui_Form
from modrinthmanager.items import Mod
from modrinthmanager.items.mod_items import Modpack
from modrinthmanager.parsers.LocalLib import LocalLib
from modrinthmanager.parsers.Modrinth import Modrinth
from modrinthmanager.utils.threads import Thread
from modrinthmanager.utils.utils import get_mod_preview, save_version, check_version_exists


class ModpacksWidget(QWidget):

    _progress_signal = Signal(Mod)

    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.mods: list[Mod] = []
        self.catalog = LocalLib()
        self._progress_signal.connect(self.update_download_info)
        self._download_all_thread = Thread(target=self.download_all, callback=self.finish_download_info)

        self.ui.download.clicked.connect(self.start_download)

    def setup(self):
        self.update_content()

    def update_content(self):
        self.ui.items_list.clear()
        self.mods = self.catalog.search_mods()
        for mod in self.mods:
            item = QListWidgetItem(mod.get_name())
            item.setIcon(get_mod_preview(mod))
            self.ui.items_list.addItem(item)

    @Slot()
    def start_download(self):
        self._download_all_thread.terminate()
        self._download_all_thread.wait()
        if self.ui.version_line.text() and self.ui.modloader_line.text():
            self.ui.download_progress.setMaximum(len(self.mods))
            self._download_all_thread.start()
        else:
            self.ui.cur_mod.setText("Enter modloader name and minecraft version")

    def update_download_info(self, mod):
        self.ui.cur_mod.setText(mod.get_name())
        self.ui.download_progress.setValue(self.mods.index(mod) + 1)

    def finish_download_info(self):
        self.ui.cur_mod.setText("Complete")
        self.ui.download_progress.setMaximum(0)
        self.ui.download_progress.setValue(0)

    def download_all(self):
        version = self.ui.version_line.text()
        loader = self.ui.modloader_line.text()
        for mod in self.mods:
            self._progress_signal.emit(mod)
            modpack = Modpack(mod.get_name(), version, loader, [])
            mod_versions = Modrinth.get_versions(mod, modpack)
            if mod_versions:
                mod_version = mod_versions[0]
                if not check_version_exists(modpack, mod_version):
                    save_version(modpack, mod_version, Modrinth.get_version(mod_version))