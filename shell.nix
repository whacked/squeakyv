{ pkgs ? import <nixpkgs> {} }:
let
  helpers = import (
    builtins.fetchurl {
      url = "https://raw.githubusercontent.com/whacked/setup/8456be0b795f18d2653769ddf70e2a3ccc86ce5b/nix/helpers.nix";
      sha256 = "134i4x9vks0s1gnxw65gxkbw03226ghv8f5r7fzppyz5rx15mg5p";
    });
  sdflow = (builtins.getFlake "github:whacked/sdflow").packages.${pkgs.system}.default;

in helpers.mkShell [
] {
  buildInputs = [
    pkgs.jq
    pkgs.jsonnet
    pkgs.python3Packages.ipython
  ] ++ [
    sdflow
    pkgs.bash
    pkgs.nodejs
    pkgs.rlwrap
    pkgs.python3
    pkgs.python3Packages.aiosql
    pkgs.python3Packages.jinja2
    pkgs.python3Packages.jsonref
  ];  # join lists with ++

  nativeBuildInputs = [
    ~/setup/bash/nix_shortcuts.nix.sh
  ];

  shellHook = ''
    LD_LIBRARY_PATH=${pkgs.lib.makeLibraryPath [
    ]}''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}

  '' + ''
    eval "$(sdflow --completions bash)"
    echo-shortcuts ${__curPos.file}
  '';  # join strings with +
}
