import json
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog


class BotLexApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BotLex — Gestionnaire d'intents")
        self.root.geometry("500x300")
        self.root.resizable(False, False)

        self.title_label = tk.Label(root, text="BotLex", font=("Helvetica", 24, "bold"))
        self.title_label.pack(pady=10)

        self.subtitle = tk.Label(root, text="Gérez et fusionnez vos fichiers d’intents JSON", font=("Helvetica", 12))
        self.subtitle.pack()

        self.generate_button = tk.Button(root, text="📝 Générer un fichier d’intents", command=self.generate_intent_file, width=40)
        self.generate_button.pack(pady=20)

        self.merge_button = tk.Button(root, text="🔗 Fusionner plusieurs fichiers", command=self.merge_intent_files, width=40)
        self.merge_button.pack()

    def get_input_list(self, prompt):
        items = []
        while True:
            val = simpledialog.askstring("Saisie", f"{prompt} (laisser vide pour finir)")
            if not val:
                break
            items.append(val)
        return items

    def generate_intent_file(self):
        filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not filename:
            return

        intents = []
        while True:
            tag = simpledialog.askstring("Nouvelle intention", "Nom de l’intention (laisser vide pour terminer):")
            if not tag:
                break

            patterns = self.get_input_list(f"Exemples pour '{tag}'")
            responses = self.get_input_list(f"Réponses pour '{tag}'")

            intents.append({
                "tag": tag,
                "patterns": patterns,
                "responses": responses
            })

        if intents:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump({"intents": intents}, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Succès", f"Fichier '{filename}' généré avec {len(intents)} intentions.")
        else:
            messagebox.showinfo("Info", "Aucune intention créée.")

    def load_intents(self, filename):
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("intents", [])

    def merge_intent_files(self):
        files = filedialog.askopenfilenames(filetypes=[("JSON files", "*.json")])
        if not files:
            return

        merged = {}

        for file in files:
            intents = self.load_intents(file)
            for intent in intents:
                tag = intent["tag"]
                if tag not in merged:
                    merged[tag] = {"patterns": set(), "responses": set()}
                merged[tag]["patterns"].update(intent["patterns"])
                merged[tag]["responses"].update(intent["responses"])

        final_intents = [
            {
                "tag": tag,
                "patterns": list(data["patterns"]),
                "responses": list(data["responses"])
            }
            for tag, data in merged.items()
        ]

        output_file = filedialog.asksaveasfilename(defaultextension=".json", initialfile="merged_intents.json", filetypes=[("JSON files", "*.json")])
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump({"intents": final_intents}, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Succès", f"{output_file} généré avec {len(final_intents)} intentions fusionnées.")

# Lancement de l’interface
if __name__ == "__main__":
    root = tk.Tk()
    app = BotLexApp(root)
    root.mainloop()
