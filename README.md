# NGPCraft Shmup Demo

This project is a small **technical demo** developed for the **Neo Geo Pocket Color**.

⚠️ This is **NOT a complete game**.

The goal of this project is to demonstrate several systems currently being developed for the upcoming **NGPCraft Engine**.

The ROM has been **tested on real Neo Geo Pocket Color hardware** as well as in emulators.

---

<img width="160" height="152" alt="Stargunner" src="https://github.com/user-attachments/assets/1ff5bb2c-cc89-4b5f-84d6-ee3b5fc8b0f5" />

# About the Demo

This demo was built using a **custom development template** currently under development.

This template will be released publicly in the future as part of the **NGPCraft Engine**, a project aiming to provide modern tools and documentation for Neo Geo Pocket Color homebrew development.

The demo is mainly used to validate different systems of the engine in a real gameplay context.

Currently implemented features include:

- player movement and shooting
- Power-up system
- enemy spawning
- stage progression
- background music
- sound effects
- basic gameplay systems
- save
- level 3 infinite

The project is still **work in progress** and should be considered a **technical showcase**, not a finished game.

---

# Audio System

All **BGM (music)** and **SFX (sound effects)** in this demo were created using:

**NGPC Sound Creator**

The music and sound effects are played in-game through a **custom sound driver** designed specifically for the Neo Geo Pocket Color hardware.

Audio workflow used in this project:

NGPC Sound Creator → Custom Sound Driver → Game Engine

Both the **audio tool** and the **sound driver** are part of the larger **NGPCraft ecosystem** currently under development.

---

# Graphics / Assets

Some graphical assets used in this demo originate from the following asset pack:

https://dan-velasquez-art.itch.io/

These assets were **modified and adapted** in order to meet the technical constraints of the **Neo Geo Pocket Color**, including:

- palette reduction
- sprite size adjustments
- tile conversion
- optimization for NGPC hardware limitations

---

# Stage 2 Technical Detail

The second stage of the demo introduces a different background rendering technique.

It uses **DMA transfers** to handle the scrolling background, allowing more advanced background behavior while keeping CPU usage low.

This is part of the ongoing experimentation and validation of the NGPCraft engine systems.

---

# NGPCraft Engine

This demo is part of a larger project currently under development:

**NGPCraft Engine**

The project aims to provide modern development resources for the Neo Geo Pocket Color, including:

- a modern NGPC development template
- a custom sound driver
- NGPC Sound Creator (music and SFX tool)
- documentation and development resources

The goal is to make **Neo Geo Pocket Color homebrew development easier and more accessible**.

---

# Credits

Original/Base Assets by  
**DanVelasquezArt**  
https://dan-velasquez-art.itch.io/

Assets were modified to meet **Neo Geo Pocket Color hardware constraints**.

---

# Status

Technical demo — Work in progress
