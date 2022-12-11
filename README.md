Italian Swirls 🍝
=================

Minimal Python language server, based on [Jedi][jedi] and [pygls][pygls].

[jedi]: https://jedi.readthedocs.io/en/latest/index.html
[pygls]: https://pygls.readthedocs.io/en/latest/index.html

Still in development but works on my machine. ✨

Supported features:

| LSP method                    | Description                |
|-------------------------------|----------------------------|
| `textDocument/completion`     | Complete                   |
| `textDocument/definition`     | Go to definition           |
| `textDocument/typeDefinition` | Go to type definition      |
| `textDocument/hover`          | Show documentation         |
| `textDocument/references`     | Show references            |
| `textDocument/rename`         | Renaming symbols and files |



Install
-------

You can either clone and build the server package from this repository, or
install it from PyPI:

```bash
pip install italianswirls
```

The only dependencies are pygls and Jedi.

Because Jedi is able to detect which environment it is installed in and which
environment is the project you're working on in, you do not need to install in
every virtualenv where it might be handy; a global user (or root) installation
should be sufficient to work regardless of your current virtualenv.

Refer to your client documentation on how to setup a server. Yes I have no idea
how to do it; to use it in Neovim and its native LSP client, I forked
[nvim-lspconfig][lspconfig-fork] to add my own config file. If it gains
attraction I might submit a PR.

[lspconfig-fork]: https://github.com/Dece/nvim-lspconfig

Example lspconfig server configuration:

```lua
local util = require 'lspconfig.util'
local root_files = { 'pyproject.toml', 'setup.cfg' }

return {
  default_config = {
    cmd = { 'italianswirls' },
    filetypes = { 'python' },
    root_dir = util.root_pattern(unpack(root_files)),
    single_file_support = true,
  },
  docs = {
    description = "Minimal Python language server based on Jedi",
    default_config = {
      root_dir = "vim's starting directory",
    },
  },
}
```



About
-----

### Why?

General-purpose servers (e.g. pyls, py-lsp) try to do too much and break stuff
too often for me. Locking Neovim when I press tab, crashes of all kind,
LspRestart failing. Also I like my linting and formatting done by dedicated
tools such as [nvim-lint][nvim-lint] and [formatter][formatter].

[nvim-lint]: https://github.com/mfussenegger/nvim-lint
[formatter]: https://github.com/mhartington/formatter.nvim

Other Jedi-based servers (e.g. jedi-language-server) seem to focus on coc-nvim
and frequently fail on Neovim's native LSP client for me. I tried to fix
jedi-language-server several times when it failed me but I thought it could be
fun to try pygls to redo it as small and simple as I can. And running a Node
server to get Python completions? No way. That said, jedi-language-server is a
good project and if you're fine with coc-nvim you should definitely check it
out. Lots of the code here is ~~stolen~~ inspired from this project.

### Why the name?

Take the string “Is this a Star Wars reference?” Language Server, compress it to
`ITASWRLS` and expand it back to Italian Swirls. Italian dishes are made of few
elements that work well together. Enough questions!

### License

GPLv3.
