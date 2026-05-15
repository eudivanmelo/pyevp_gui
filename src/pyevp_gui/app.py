import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from pylibevp import LibEVP

class EVPManagerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("PyEVP GUI")
        self.geometry("600x500")
        self.minsize(600, 500)
        self.evp = LibEVP()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.tabs = ctk.CTkTabview(self, segmented_button_selected_color="#3b8ed0")
        self.tabs.grid(row=1, column=0, sticky="nsew", padx=16, pady=16)

        self.tab_extract = self.tabs.add("Extract")
        self.tab_pack = self.tabs.add("Pack")

        self.setup_extract_ui()
        self.setup_pack_ui()

        self.console_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="#0c0c0c")
        self.console_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 16))

        self.console = ctk.CTkTextbox(
            self.console_frame,
            font=("Consolas", 12),
            fg_color="transparent",
            text_color="#00FF00",
        )
        self.console.pack(fill="both", expand=True, padx=8, pady=8)

        self.log("System ready. Select an operation.")

    def log(self, message, level="INFO"):
        self.console.insert("end", f"[{level}] {message}\n")
        self.console.see("end")

    def create_input_group(self, master, label_text, variable, command, btn_text="Procurar"):
        """Build an input row with label, entry, and action button."""
        container = ctk.CTkFrame(master, fg_color="transparent")
        container.pack(fill="x", padx=8, pady=4)

        ctk.CTkLabel(container, text=label_text, font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")

        row = ctk.CTkFrame(container, fg_color="transparent")
        row.pack(fill="x", pady=1)

        entry = ctk.CTkEntry(row, textvariable=variable, placeholder_text="Path...")
        entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        btn = ctk.CTkButton(row, text=btn_text, width=100, command=command)
        btn.pack(side="right")
        return entry

    def setup_extract_ui(self):
        self.extract_input_path = ctk.StringVar()
        self.extract_output_path = ctk.StringVar()

        self.create_input_group(
            self.tab_extract, "Archive (.evp):",
            self.extract_input_path, self.browse_evp_file
        )

        self.create_input_group(
            self.tab_extract, "Output directory:",
            self.extract_output_path, self.browse_output_dir
        )

        self.btn_run_extract = ctk.CTkButton(
            self.tab_extract,
            text="RUN EXTRACTION",
            height=32,
            font=ctk.CTkFont(weight="bold"),
            fg_color="#28a745",
            hover_color="#218838",
            command=self.run_extract
        )
        self.btn_run_extract.pack(pady=16, padx=8, fill="x")

    def setup_pack_ui(self):
        self.pack_base_path = ctk.StringVar()
        self.pack_output_file = ctk.StringVar()

        self.create_input_group(
            self.tab_pack, "Base directory:",
            self.pack_base_path, self.browse_base_dir
        )

        self.create_input_group(
            self.tab_pack, "Output archive:",
            self.pack_output_file, self.browse_save_evp, "Save as"
        )

        self.btn_run_pack = ctk.CTkButton(
            self.tab_pack,
            text="GENERATE EVP",
            height=32,
            font=ctk.CTkFont(weight="bold"),
            command=self.run_pack
        )
        self.btn_run_pack.pack(pady=16, padx=8, fill="x")

    def browse_evp_file(self):
        f = filedialog.askopenfilename(filetypes=[("EVP Files", "*.evp")])
        if f:
            self.extract_input_path.set(f)

    def browse_output_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.extract_output_path.set(d)

    def browse_base_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.pack_base_path.set(d)

    def browse_save_evp(self):
        f = filedialog.asksaveasfilename(defaultextension=".evp", filetypes=[("EVP Files", "*.evp")])
        if f:
            self.pack_output_file.set(f)

    def run_extract(self):
        archive, output = self.extract_input_path.get(), self.extract_output_path.get()
        if not archive or not output:
            messagebox.showwarning("Warning", "Select archive and output directory.")
            return

        self.btn_run_extract.configure(state="disabled", text="Extracting...")

        def task():
            try:
                self.log(f"Lendo índice de: {Path(archive).name}...")
                files = self.evp.get_archive_files(archive)

                if not files:
                    self.log("Arquivo vazio ou invalido.", "WARN")
                else:
                    self.log(f"Preparando extracao de {len(files)} arquivos...")

                res = self.evp.unpack(archive, output)

                if res.get("success"):
                    for i, file_info in enumerate(files):
                        filename = file_info.get("file") or file_info.get("filename")
                        self.log(f"Extraído [{i+1}/{len(files)}]: {filename}")

                    self.log(f"✓ Concluído: {res['message']}", "SUCCESS")
                else:
                    self.log(res.get("message", "Erro desconhecido"), "ERROR")

            except Exception as e:
                self.log(f"Erro crítico: {str(e)}", "ERROR")

            finally:
                self.btn_run_extract.configure(state="normal", text="RUN EXTRACTION")

        threading.Thread(target=task, daemon=True).start()

    def _collect_files_to_pack(self, base: Path) -> list[str]:
        return [str(path.relative_to(base)) for path in base.rglob("*") if path.is_file()]

    def run_pack(self):
        base, output = self.pack_base_path.get(), self.pack_output_file.get()
        if not base or not output:
            messagebox.showwarning("Warning", "Select base directory and output file.")
            return

        self.btn_run_pack.configure(state="disabled", text="Packing...")

        def task():
            self.log(f"Compactando diretório: {Path(base).name}")

            try:
                base_path = Path(base)
                files = self._collect_files_to_pack(base_path)
                if not files:
                    self.log("Nenhum arquivo encontrado para compactar.", "WARN")
                    return

                res = self.evp.pack(str(base_path), files, output)
                self.log(res["message"], "SUCCESS" if res["success"] else "ERROR")
            except Exception as exc:
                self.log(f"Erro critico: {exc}", "ERROR")
            finally:
                self.btn_run_pack.configure(state="normal", text="GENERATE EVP")

        threading.Thread(target=task, daemon=True).start()


def main() -> int:
    app = EVPManagerGUI()
    app.mainloop()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())