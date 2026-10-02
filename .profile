# ~/.profile: executed by Bourne-compatible login shells.

if [ "$BASH" ]; then
  if [ -f ~/.bashrc ]; then
    . ~/.bashrc
  fi
fi


# Added by Antigravity CLI installer
export PATH="/root/.local/bin:$PATH"
