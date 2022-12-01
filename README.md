Italian Swirls 🍝
=================

Minimal Python language server, based on [Jedi][jedi] and [pygls][pygls].

[jedi]: https://jedi.readthedocs.io/en/latest/index.html
[pygls]: https://pygls.readthedocs.io/en/latest/index.html

WIP.



About
-----

### Why?

General-purpose servers (pyls, py-lsp) try to do too much and break stuff too
often for me. Locking Neovim when I press tab, crashes of all kind, LspRestart
failing. Also I like my linting and formatting done by dedicated tools such as
[nvim-lint][nvim-lint] and [formatter][formatter].

[nvim-lint]: https://github.com/mfussenegger/nvim-lint
[formatter]: https://github.com/mhartington/formatter.nvim

Other Jedi-based servers seem to focus on coc-nvim and frequently fail on
Neovim's native LSP client for me. I tried to fix jedi-language-server several
times when it failed me but thought it could be fun to try pygls to redo it as
small and simple as I can. And running a Node server to get Python completions?
HA!

### Why the name?

Take the string “Is this a Star Wars reference?” Language Server, compress it to
`ITASWRLS` and expand it back to Italian Swirls. Italian dishes are made of few
elements that work well together. Enough questions!
