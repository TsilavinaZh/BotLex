import tkinter as tk
from tkinter import scrolledtext, messagebox
from tkinter import ttk
import json, os, re, random, traceback
import numpy as np
from datetime import datetime

MUTE = False
SESSION_LOG = []

def load_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def tokenize(text):
    return re.findall(r'\b\w+\b', text.lower())

def build_vocab(intents):
    vocab = set()
    for intent in intents:
        for pattern in intent["patterns"]:
            vocab.update(tokenize(pattern))
    return sorted(vocab)

def text_to_vector(text, vocab):
    tokens = tokenize(text)
    return np.array([tokens.count(word) for word in vocab])

def cosine_similarity(v1, v2):
    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def predict_multiple_intents(text, intents, vocab, threshold=0.3):
    input_vector = text_to_vector(text, vocab)
    found_tags = set()
    for intent in intents:
        for pattern in intent["patterns"]:
            pattern_vector = text_to_vector(pattern, vocab)
            if cosine_similarity(input_vector, pattern_vector) >= threshold:
                found_tags.add(intent["tag"])
                break
    return list(found_tags)

# def detect_python_code(text):
#     keywords = ["def", "print", "for", "while", "if", "else", "elif", "return", "import", "class"]
#     return any(kw in text for kw in keywords)

def try_exec(code):
    try:
        exec(code, {})
        return None
    except Exception:
        return traceback.format_exc()

def auto_correct(code):
    corrections = []
    corrected = code
    pattern = r'print([^"\')]+)'
    matches = re.findall(pattern, corrected)
    for m in matches:
        if not m.strip().startswith('"'):
            corrections.append(f'- Ajout de guillemets dans `print({m})`')
        corrected = re.sub(pattern, r'print("\1")', corrected)
    lines = corrected.splitlines()
    for i, line in enumerate(lines):
        if re.match(r'^\s*(def|if|for|while|else|elif|class)\b.*[^:]\s*$', line):
            lines[i] = line.rstrip() + ':'
            corrections.append(f'- Ajout de ":" à la ligne `{line.strip()}`')
    return '\n'.join(lines), corrections

def debug_and_correct(code):
    error_before = try_exec(code)
    if not error_before:
        return " Votre code fonctionne correctement."
    suggestion, corrections = auto_correct(code)
    error_after = try_exec(suggestion)
    if not error_after:
        return "Code corrigé :\n" + "\n".join(corrections) + "\n\n🔧 Nouveau code :\n" + suggestion
    return f"Erreur détectée dans votre code :\n{error_before}"

def show_help():
    return (
        "Commandes disponibles :\n"
        " - !help           → Affiche cette aide\n"
        " - !mute / !unmute → Active/désactive les réponses\n"
        " - exit            → Fermer l'application"
    )

def get_example(tag, intents):
    for i in intents:
        if i["tag"] == tag:
            return random.choice(i["patterns"])
    return "Aucun exemple trouvé."

def save_log():
    if not os.path.exists("logs"):
        os.makedirs("logs")
    filename = datetime.now().strftime("logs/session_%Y%m%d_%H%M%S.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(SESSION_LOG, f, indent=2, ensure_ascii=False)


class ChatbotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BotLex - Assistant IA")
        self.root.geometry("900x650")
        self.root.configure(bg="#0f111a")

        self.data = load_data("data.json")
        self.intents = self.data["intents"]
        self.vocab = build_vocab(self.intents)

        # En-tête
        header = tk.Label(root, text="BotLex - Assistant IA", 
                          font=("Segoe UI Semibold", 16), bg="#0f111a", fg="#00ffd5", pady=20)
        header.pack()

        # Zone de texte
        self.text_area = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, bg="#1e1e2e", fg="#f5f5f5",
            font=("Consolas", 13), padx=10, pady=10,
            borderwidth=0, highlightthickness=0
        )
        self.text_area.pack(padx=20, pady=(0,10), fill=tk.BOTH, expand=True)
        self.text_area.config(state=tk.DISABLED)

        # Entrée utilisateur
        self.entry = tk.Entry(root, font=("Segoe UI", 13), bg="#2d2d3a", fg="#ffffff",
                              insertbackground="#ffffff", borderwidth=0, relief=tk.FLAT)
        self.entry.pack(padx=20, pady=(0, 10), fill=tk.X)
        self.entry.bind("<Return>", self.send)

        # Boutons
        button_frame = tk.Frame(root, bg="#0f111a")
        button_frame.pack(pady=5)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("TButton",
                        font=("Segoe UI", 10),
                        foreground="#ffffff",
                        background="#3c3f58",
                        borderwidth=0,
                        focusthickness=3,
                        focuscolor="none",
                        padding=6)
        style.map("TButton",
                  background=[("active", "#4d5172")])

        buttons = [
            ("Envoyer", self.send),
            ("Aide", self.show_help),
            ("Mute", self.mute),
            ("Unmute", self.unmute),
            ("Quitter", self.quit)
        ]

        for label, command in buttons:
            ttk.Button(button_frame, text=label, command=command).pack(side=tk.LEFT, padx=6)

    def print_to_chat(self, sender, message):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.insert(tk.END, f"{sender} : {message}\n\n")
        self.text_area.see(tk.END)
        self.text_area.config(state=tk.DISABLED)

    def send(self, event=None):
        global MUTE
        user_input = self.entry.get().strip()
        if not user_input:
            return
        self.print_to_chat("👤 Vous", user_input)
        self.entry.delete(0, tk.END)

        if user_input == "exit":
            save_log()
            self.root.quit()
            return

        response = ""

        if user_input == "!help":
            response = show_help()
        elif user_input == "!mute":
            MUTE = True
            response = "🔇 Mode silencieux activé."
        elif user_input == "!unmute":
            MUTE = False
            response = "🔊 Mode silencieux désactivé."
        elif user_input.startswith("!example"):
            parts = user_input.split()
            if len(parts) > 1:
                response = get_example(parts[1], self.intents)
            else:
                response = "Utilisez : !example <tag>"
        # elif detect_python_code(user_input):
        #     response = debug_and_correct(user_input)
        else:
            tags = predict_multiple_intents(user_input, self.intents, self.vocab)
            if tags:
                for t in tags:
                    for i in self.intents:
                        if i["tag"] == t:
                            response += random.choice(i["responses"]) + " "
            else:
                response = "Je n’ai pas compris votre demande."

        SESSION_LOG.append({"user": user_input, "ai": response})
        if not MUTE:
            self.print_to_chat("🤖 AI", response)

    def show_help(self):
        self.print_to_chat("🤖 AI", show_help())

    def mute(self):
        global MUTE
        MUTE = True
        self.print_to_chat("🤖 AI", "🔇 Mode silencieux activé.")
        messagebox.showinfo("Mute", "Mode silencieux activé.")

    def unmute(self):
        global MUTE
        MUTE = False
        self.print_to_chat("🤖 AI", "🔊 Mode silencieux désactivé.")
        messagebox.showinfo("Unmute", "Mode silencieux désactivé.")

    def quit(self):
        save_log()
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatbotApp(root)
    root.mainloop()