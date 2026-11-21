#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import queue
import os
import time
import shutil
import platform
from datetime import datetime

APP_NAME = "WLinux Studio"

BG = "#10151f"
PANEL = "#192333"
ACCENT = "#27c98b"
TEXT = "#e8edf5"
MUTED = "#8996aa"
RED = "#ff626c"

output_queue = queue.Queue()
running = False


class WLinuxStudio:

    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1050x720")
        self.root.minsize(850, 600)
        self.root.configure(bg=BG)

        self.create_interface()
        self.refresh_system_info()
        self.process_output()

    def create_interface(self):

        # HEADER
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=25, pady=20)

        tk.Label(
            header,
            text="WLINUX STUDIO",
            font=("Ubuntu", 25, "bold"),
            fg=ACCENT,
            bg=BG
        ).pack(side="left")

        tk.Label(
            header,
            text="SYSTEM MANAGEMENT",
            font=("Ubuntu", 10),
            fg=MUTED,
            bg=BG
        ).pack(side="left", padx=15, pady=12)

        # SYSTEM INFO
        info = tk.Frame(self.root, bg=PANEL)
        info.pack(fill="x", padx=25, pady=5)

        self.system_label = tk.Label(
            info,
            text="Ładowanie informacji o systemie...",
            font=("Ubuntu", 11),
            fg=TEXT,
            bg=PANEL,
            justify="left",
            anchor="w"
        )
        self.system_label.pack(fill="x", padx=20, pady=15)

        # MAIN AREA
        content = tk.Frame(self.root, bg=BG)
        content.pack(fill="both", expand=True, padx=25, pady=15)

        sidebar = tk.Frame(content, bg=PANEL, width=235)
        sidebar.pack(side="left", fill="y", padx=(0, 15))
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar,
            text="MENU",
            bg=PANEL,
            fg=MUTED,
            font=("Ubuntu", 10, "bold")
        ).pack(anchor="w", padx=18, pady=15)

        buttons = [
            ("🔄  Aktualizuj system", self.update_system),
            ("📦  Aktualizuj aplikacje", self.update_apps),
            ("🧹  Czyszczenie systemu", self.clean_system),
            ("🔧  Napraw DPKG", self.repair_dpkg),
            ("💾  Kopia zapasowa", self.backup),
            ("🖥  Sterowniki", self.drivers),
            ("⚙  Diagnostyka", self.diagnostics),
            ("🌐  Speedtest", self.speedtest),
            ("🚀  Aktualizacja GRUB", self.grub),
            ("📊  Dostępne aktualizacje", self.check_updates),
        ]

        for text, command in buttons:
            self.create_button(sidebar, text, command)

        # RIGHT PANEL
        right = tk.Frame(content, bg=PANEL)
        right.pack(side="right", fill="both", expand=True)

        tk.Label(
            right,
            text="CENTRUM OPERACYJNE",
            bg=PANEL,
            fg=ACCENT,
            font=("Ubuntu", 14, "bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))

        self.status = tk.Label(
            right,
            text="Gotowy do pracy",
            bg=PANEL,
            fg=TEXT,
            font=("Ubuntu", 10)
        )
        self.status.pack(anchor="w", padx=20)

        self.progress = ttk.Progressbar(
            right,
            mode="indeterminate"
        )
        self.progress.pack(fill="x", padx=20, pady=10)

        self.log = tk.Text(
            right,
            bg="#0b1019",
            fg="#b8f5d8",
            insertbackground="white",
            font=("Ubuntu Mono", 10),
            relief="flat",
            wrap="word"
        )
        self.log.pack(fill="both", expand=True, padx=15, pady=10)

        self.log.tag_config("error", foreground=RED)
        self.log.tag_config("success", foreground=ACCENT)

        # BOTTOM
        bottom = tk.Frame(self.root, bg=BG)
        bottom.pack(fill="x", padx=25, pady=15)

        tk.Label(
            bottom,
            text="WLinux Studio | Ubuntu Edition",
            bg=BG,
            fg=MUTED
        ).pack(side="left")

        tk.Button(
            bottom,
            text="RESTART SYSTEMU",
            bg="#a83242",
            fg="white",
            activebackground=RED,
            relief="flat",
            padx=15,
            pady=8,
            command=self.reboot
        ).pack(side="right")

    def create_button(self, parent, text, command):

        button = tk.Button(
            parent,
            text=text,
            command=command,
            bg=PANEL,
            fg=TEXT,
            activebackground=ACCENT,
            activeforeground="#10151f",
            relief="flat",
            anchor="w",
            padx=18,
            pady=11,
            font=("Ubuntu", 10),
            cursor="hand2"
        )

        button.pack(fill="x", padx=8, pady=2)

    def write_log(self, text, tag=None):

        self.log.insert("end", text + "\n", tag)
        self.log.see("end")

    def process_output(self):

        while not output_queue.empty():

            text = output_queue.get()
            self.write_log(text)

        self.root.after(100, self.process_output)

    def execute(self, commands, title):

        global running

        if running:
            messagebox.showwarning(
                APP_NAME,
                "Inna operacja jest już wykonywana."
            )
            return

        if not messagebox.askyesno(
            APP_NAME,
            f"Czy uruchomić operację:\n\n{title}?"
        ):
            return

        running = True

        self.status.config(text=title)
        self.progress.start(10)

        self.write_log("")
        self.write_log("=" * 55)
        self.write_log("[INFO] " + title)
        self.write_log("=" * 55)

        def worker():

            global running

            success = True

            try:
                for command in commands:

                    output_queue.put(
                        "\n$ " + " ".join(command)
                    )

                    process = subprocess.Popen(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1
                    )

                    for line in process.stdout:
                        output_queue.put(line.rstrip())

                    process.wait()

                    if process.returncode != 0:
                        output_queue.put(
                            "[ERROR] Polecenie zakończone kodem "
                            + str(process.returncode)
                        )
                        success = False
                        break

            except Exception as error:
                output_queue.put("[ERROR] " + str(error))
                success = False

            output_queue.put(
                "[SUCCESS] Operacja zakończona."
                if success
                else "[ERROR] Operacja zakończona z błędem."
            )

            self.root.after(
                0,
                lambda: self.finish_operation(success)
            )

            running = False

        threading.Thread(
            target=worker,
            daemon=True
        ).start()

    def finish_operation(self, success):

        self.progress.stop()

        self.status.config(
            text="Operacja zakończona"
            if success else "Wystąpił błąd"
        )

    def privileged(self, command):
	    return ["pkexec"] + command


    def update_system(self):

        commands = [
            self.privileged(["apt-get", "update"]),
            self.privileged([
                "apt-get", "upgrade", "-y"
            ]),
            self.privileged([
                "apt-get", "full-upgrade", "-y"
            ]),
            self.privileged([
                "apt-get", "autoremove", "-y"
            ])
        ]

        self.execute(commands, "Aktualizacja systemu")

    def update_apps(self):

        commands = []

        if shutil.which("flatpak"):
            commands.append([
                "flatpak", "update", "-y"
            ])

        if shutil.which("snap"):
            commands.append(
                self.privileged(["snap", "refresh"])
            )

        if shutil.which("pkcon"):
            commands.append(
                self.privileged([
                    "pkcon", "refresh", "force"
                ])
            )
            commands.append(
                self.privileged([
                    "pkcon", "update", "-y"
                ])
            )

        if commands:
            self.execute(commands, "Aktualizacja aplikacji")
        else:
            messagebox.showinfo(
                APP_NAME,
                "Nie znaleziono Flatpak, Snap ani PackageKit."
            )

    def clean_system(self):

        self.execute([
            self.privileged(["apt-get", "clean"]),
            self.privileged(["apt-get", "autoremove", "-y"])
        ], "Czyszczenie systemu")

    def repair_dpkg(self):

        self.execute([
            self.privileged(["dpkg", "--configure", "-a"]),
            self.privileged([
                "apt-get", "install", "-f", "-y"
            ]),
            self.privileged(["apt-get", "check"]),
            self.privileged(["dpkg", "--audit"])
        ], "Naprawa DPKG")

    def backup(self):

        if not messagebox.askyesno(
            APP_NAME,
            "Utworzyć kopię /etc, /home, /boot i EFI?\n"
            "Backup może zajmować dużo miejsca."
        ):
            return

        script = r'''
set -e
D="/backup_system_$(date +%Y-%m-%d_%H-%M-%S)"
mkdir -p "$D"
dpkg --get-selections > "$D/packages_list.txt"
apt-mark showmanual > "$D/manual_packages.txt"
cp -a /etc/apt/sources.list* "$D/" 2>/dev/null || true
tar -czpf "$D/etc_backup.tar.gz" /etc
tar -czpf "$D/home_backup.tar.gz" /home
[ ! -d /boot ] || tar -czpf "$D/boot_backup.tar.gz" /boot
[ ! -d /boot/efi ] || tar -czpf "$D/efi_backup.tar.gz" /boot/efi
cp /etc/fstab "$D/fstab.backup"
echo "Backup zapisany w: $D"
'''

        self.execute([
            self.privileged(["bash", "-c", script])
        ], "Tworzenie kopii zapasowej")

    def drivers(self):

        commands = []

        if shutil.which("ubuntu-drivers"):
            commands.append([
                "ubuntu-drivers", "devices"
            ])

        if shutil.which("lspci"):
            commands.append([
                "lspci", "-nnk"
            ])

        if commands:
            self.execute(commands, "Sprawdzanie sterowników")
        else:
            messagebox.showwarning(
                APP_NAME,
                "Brak narzędzi do sprawdzania sterowników."
            )

    def diagnostics(self):

        self.execute([
            ["df", "-h"],
            ["free", "-h"],
            ["ps", "-eo", "pid,stat,etime,comm"],
            ["systemctl", "--failed"],
            ["uname", "-a"]
        ], "Diagnostyka systemu")

    def speedtest(self):

        if not shutil.which("speedtest-cli"):
            messagebox.showinfo(
                APP_NAME,
                "Zainstaluj speedtest-cli:\n"
                "sudo apt install speedtest-cli"
            )
            return

        self.execute([
            ["speedtest-cli", "--simple"]
        ], "Test prędkości Internetu")

    def grub(self):

        if not shutil.which("update-grub"):
            messagebox.showwarning(
                APP_NAME,
                "Nie znaleziono update-grub."
            )
            return

        self.execute([
            self.privileged(["update-grub"])
        ], "Aktualizacja GRUB")

    def check_updates(self):

        self.execute([
            ["bash", "-c", "apt list --upgradable 2>/dev/null"]
        ], "Sprawdzanie dostępnych aktualizacji")

    def refresh_system_info(self):

        try:
            distro = platform.platform()
            kernel = platform.release()
            hostname = platform.node()
            user = os.environ.get("USER", "unknown")

            total, used, free = shutil.disk_usage("/")

            info = (
                f" SYSTEM: {distro}\n"
                f" KERNEL: {kernel}\n"
                f" HOST: {hostname}\n"
                f" USER: {user}\n"
                f" WOLNE MIEJSCE: {free // (1024**3)} GB"
            )

            self.system_label.config(text=info)

        except Exception as error:
            self.system_label.config(
                text="Nie udało się pobrać informacji: "
                + str(error)
            )

    def reboot(self):

        if messagebox.askyesno(
            APP_NAME,
            "Czy na pewno chcesz zrestartować komputer?"
        ):
            subprocess.Popen([
                "pkexec", "systemctl", "reboot"
            ])


if __name__ == "__main__":

    root = tk.Tk()
    app = WLinuxStudio(root)
    root.mainloop()
