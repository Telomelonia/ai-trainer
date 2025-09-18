# AI Trainer Thing
## Hackathon Project That Actually Works (Somehow)

### What Is This?
A core stability training app with AI coaching. Made for some Internet of Agents hackathon. Works better than expected, which is concerning.

### What It Does
- Streamlit app (because I'm lazy and it's fast)
- Fake Arduino data (real hardware is overrated)  
- AI coach that judges your form
- Progress tracking for people who care about that
- Multiple pages because apparently that's "professional"

### Running This Thing

#### Setup (The Boring Part)
```bash
# Virtual env is already there, just activate it
source hackathon_env/bin/activate

# Install stuff (probably already done but whatever)
pip install -r requirements.txt
```

#### Actually Run It
```bash
# The simple way
streamlit run app/main.py

# Or if you're feeling fancy
./run_app.sh
```

Go to `localhost:8501` and click around. There are 4 pages because I thought that was impressive at 3 AM.

### File Structure (For Future Me)
```
ai-trainer/
├── app/main.py           # The main thing
├── mcp_servers/          # MCP stuff (Phase 2)
├── agents/               # AI agents (Phase 3)  
├── requirements.txt      # Dependencies I forgot about
└── hackathon_env/        # Python venv
```

### Technical Stuff
- **Fake Arduino**: Generates random but believable stability data
- **Real-time Updates**: Because apparently that's impressive
- **AI Coaching**: GPT pretends to be a fitness instructor
- **Charts**: People love charts

### Current Status
Phase 3 complete. Agent system works. MCP servers exist. Everything talks to everything else somehow. Ready for Phase 4 whenever I feel like it.

---
*Built during a hackathon when I should have been sleeping*