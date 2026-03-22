# ez-ha zsh configuration — adapted from rex's dotfiles
# ---------------------------------------------------------------------------

# Source HA environment (API tokens, aliases, env vars)
[ -f /etc/profile.d/ha-env.sh ] && source /etc/profile.d/ha-env.sh

# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------
HISTFILE=/data/zsh_history
HISTSIZE=10000
SAVEHIST=10000
setopt HIST_IGNORE_DUPS
setopt HIST_IGNORE_SPACE
setopt SHARE_HISTORY
setopt APPEND_HISTORY
setopt INC_APPEND_HISTORY

# ---------------------------------------------------------------------------
# Plugins
# ---------------------------------------------------------------------------
# Autosuggestions (ghost text from history)
[ -f /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh ] && \
  source /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh

# Syntax highlighting (command coloring)
[ -f /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ] && \
  source /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh

# History substring search (type partial command, press up/down to search)
[ -f /usr/share/zsh/plugins/zsh-history-substring-search/zsh-history-substring-search.zsh ] && \
  source /usr/share/zsh/plugins/zsh-history-substring-search/zsh-history-substring-search.zsh

# ---------------------------------------------------------------------------
# Key bindings
# ---------------------------------------------------------------------------
bindkey '^[[A' history-substring-search-up
bindkey '^[[B' history-substring-search-down

# ---------------------------------------------------------------------------
# Aliases — modern ls with eza
# ---------------------------------------------------------------------------
alias ls='eza --color=always --icons=always --group-directories-first'
alias ll='eza -la --color=always --icons=always --group-directories-first'
alias la='eza -a --color=always --icons=always --group-directories-first'
alias lt='eza --tree --level=2 --color=always --icons=always'

# ---------------------------------------------------------------------------
# Git aliases
# ---------------------------------------------------------------------------
alias s='git status -sb'
alias ga='git add -A'
alias gap='git add -p'
alias gbr='git branch -v'
alias gco='git checkout'
alias gd='git diff -M'
alias gdc='git diff --cached -M'
alias gf='git fetch'
alias glog='git log --date-order --pretty="format:%C(yellow)%h%Cblue%d%Creset %s %C(white) %an, %ar%Creset"'
alias gl='glog --graph'
alias gla='gl --all'
alias gp='git push'
alias grb='git rebase -p'
alias grba='git rebase --abort'
alias grbc='git rebase --continue'
alias gr='git reset'
alias grv='git remote -v'
alias gs='git show'
alias gst='git stash'
alias gstp='git stash pop'
alias gup='git pull'

# Tmux
alias tm='tmux attach -t main || tmux new -s main'

# Reload shell
alias src='exec zsh'

# ---------------------------------------------------------------------------
# Git helper functions
# ---------------------------------------------------------------------------
gc() {
  git diff --cached | grep '\btap[ph]\b' >/dev/null &&
    echo "\e[0;31;29mOops, there's a #tapp or similar in that diff.\e[0m" ||
    git commit -v "$@"
}

git_current_branch() {
  cat "$(git rev-parse --git-dir 2>/dev/null)/HEAD" | sed -e 's/^.*refs\/heads\///'
}

alias gpthis='gp origin $(git_current_branch)'

# ---------------------------------------------------------------------------
# FZF
# ---------------------------------------------------------------------------
[ -f /usr/share/fzf/key-bindings.zsh ] && source /usr/share/fzf/key-bindings.zsh
[ -f /usr/share/fzf/completion.zsh ] && source /usr/share/fzf/completion.zsh

# ---------------------------------------------------------------------------
# Starship prompt
# ---------------------------------------------------------------------------
eval "$(starship init zsh)"
