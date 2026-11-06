# ICT 2024 Mentorship AI Skill

**Turn Claude (or any large language model) into an elite, no-nonsense ICT 2024 trading mentor.**

## 📖 Overview
This repository contains a fully synthesized, 21-lecture knowledge base derived from the Inner Circle Trader (ICT) 2024 Mentorship. All 21 video transcripts were manually processed to extract the core algorithmic trading mechanics, risk management models, and trading psychology. All personal anecdotes, rants, and side-talk have been filtered out.

The result is a highly condensed, 15,000-token "Master Skill" file (`SKILL.md`) designed to be plugged directly into an AI model's system prompt.

## 🚀 How to Use the AI Skill

### For Claude (or Custom GPTs)
1. Open the [`SKILL.md`](./SKILL.md) file in this repository.
2. Copy the **entire contents** of the file.
3. Paste the text into the **System Prompt**, **Project Knowledge**, or **Custom Instructions** box of your AI platform (like Claude Projects, OpenAI Custom GPTs, or Poe).
4. In your chat, simply type `/ict2024mentorship` to immediately activate the persona.

Once activated, the AI will exclusively use the terminology, definitions, and logic of the 2024 Mentorship. It will strictly avoid retail concepts (like RSI or Elliott Wave) and act as a disciplined, risk-conscious mentor.

## 🗂 Repository Structure
- **`SKILL.md`**: The master AI prompt and fused knowledge base. **(This is the only file you need to power the AI).**
- **`Summaries/`**: A folder containing the individual markdown summaries for all 21 lectures. Useful if you want to read the concepts chronologically.
- **`build_skill.js`**: A small Node.js script used to compile the individual lecture summaries into the master `SKILL.md` file.

## 📝 Key Concepts Included
- The Power of 3 (AMD) & The Judas Swing
- 7:00 AM, 8:00 AM, and 9:30 AM Macros & Spooling
- New Day / New Week Opening Gaps (NDOG & NWOG)
- The 5-to-1 Gearing Model & Dynamic Trail Partials
- The Institutional Order Entry Drill (IOED)
- Pre-Holiday & High-Resistance Market Environments

## ⚖️ Disclaimer
This project is for educational purposes only. It is not financial advice, and the AI should not be used to generate live buy/sell signals. The concepts are based on the teachings of The Inner Circle Trader.
