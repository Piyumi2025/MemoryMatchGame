Here’s a well-structured **README.md** file for your GitHub project. I’ve included sections that explain the game, its features, setup instructions, and usage. You can copy it directly into your repo:

````markdown
# Memory Match — 32 Levels

A visually appealing **Memory Match Game** built with Python and Pygame. Test your memory skills across **32 challenging levels**, track your best times, and enjoy smooth animations and sound effects!

---

## 🎮 Game Overview

Memory Match is a classic card-matching game where the player flips over cards to find matching pairs. This version includes:

- **32 Levels** of increasing difficulty
- **Time & Moves Tracking**
- **High Score Saving** for each level
- Smooth **animations & sound effects**
- Background music and interactive buttons
- Responsive card layout that scales with the window
- Logo and polished UI design

---

## 🖼️ Assets

The project uses three folders:

- `images/` — Card faces and back images (`1.png` to `32.png`, `back.png`)
- `sounds/` — Sound effects (`flip.wav`, `match.wav`, `mismatch.wav`, `win.wav`, `button.wav`)
- `assets/` — Font (`font.ttf`), background music (`bg_music.mp3`), logo (`logo.png`), and `high_scores.json` for storing scores

> Note: If any asset is missing, the game provides placeholders.

---

## 🛠️ Requirements

- Python 3.10+
- [Pygame](https://www.pygame.org/) library

Install Pygame using:

```bash
pip install pygame
````

---

## 🚀 How to Run

1. Clone the repository:

```bash
git clone https://github.com/Piyumi2025/MemoryMatchGame
cd memory-match-32-levels
```

2. Ensure the folders `images`, `sounds`, and `assets` are present with the required files.

3. Run the game:

```bash
python main.py
```

4. Controls:

* **Mouse Click** — Flip cards
* **ESC** — Return to Home screen
* **H** — View High Scores
* **SPACE / ENTER** — Start game from Home

---

## 📁 Folder Structure

```
memory-match-32-levels/
│
├─ images/
│   ├─ back.png
│   ├─ 1.png
│   ├─ 2.png
│   └─ ... up to 32.png
│
├─ sounds/
│   ├─ flip.wav
│   ├─ match.wav
│   ├─ mismatch.wav
│   ├─ win.wav
│   └─ button.wav
│
├─ assets/
│   ├─ font.ttf
│   ├─ bg_music.mp3
│   ├─ logo.png
│   └─ high_scores.json
│
├─ main.py
└─ README.md
```

---

## 🎨 Features & Screenshots

* **Dynamic Card Layout:** Cards scale to fit the window based on the number of pairs
* **High Scores Tracking:** Save best times per level
* **Interactive Buttons:** Hover effects and sounds
* **Animated Flip & Match:** Visual feedback for matches and mismatches
* **Background Music & Sound Effects:** Enhance gameplay experience

---

## 🔧 Notes

* If a card image or sound is missing, the game will generate a placeholder and continue running.
* High scores are automatically saved in `assets/high_scores.json`.
* The game plays background music in a loop. Volume can be adjusted in `main.py`.

---

## 📌 License

This project is open-source and free to use under the MIT License.

---

Enjoy testing your memory and climbing all **32 levels**! 🧠💡

```

I can also make a **shorter, GitHub-friendly version with badges and demo GIF placeholders** if you want it to look more professional.  

Do you want me to create that enhanced version too?
```
