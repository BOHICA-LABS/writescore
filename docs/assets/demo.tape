# VHS Tape for WriteScore Demo
# Run with: vhs docs/assets/demo.tape

Output docs/assets/demo.gif

Set FontSize 12
Set Width 900
Set Height 800
Set Theme "Dracula"
Set Padding 10
Set TypingSpeed 50ms

# Hide python environment setup
Hide
Type "source .venv/bin/activate"
Enter
Sleep 800ms

# Pipe to less with color support, start at beginning
Show
Type "writescore analyze tests/fixtures/sample_human_text.md --mode fast 2>&1 | less -R"
Enter

# Wait for less to load
Sleep 10s

# Go to top of output
Type "g"
Sleep 6s

# Scroll down through output using space (page down in less)
# ~5 pages at 6 seconds each = 30 seconds total
Space
Sleep 6s
Space
Sleep 6s
Space
Sleep 6s
Space
Sleep 6s
Space
Sleep 6s

# Quit less
Type "q"
Sleep 500ms
