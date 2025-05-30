let
  pkgs = import <nixpkgs> {};
  pymrio = pkgs.callPackage /Users/tterimaa/code/projects/pymrio/default.nix {};
in

pkgs.mkShell {
  buildInputs = with pkgs.python3Packages; [
    jupyter
    pandas
    numpy
    matplotlib
    openpyxl
    pycountry
    pymrio
  ];
}
