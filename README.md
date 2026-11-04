# nxnative iOS — Pokopia

This repository is a source snapshot of the `nxnative` iOS runtime and the Pokémon Pokopia game profile used to build a local iPhone app. It includes the runtime changes for command record validation, RomFS index bounds, and the partial iOS shader build workflow.

The app was built and installed on an iPhone Air with an existing partial shader library. The full shader build and gameplay validation are separate work; this snapshot is not a prebuilt app.

## Source and attribution

This snapshot is based on [`seedds/nxnative`](https://github.com/seedds/nxnative) at commit `a3d85ae1259e4cb59b3bc941010e09f8a7159650`, with the local iOS and safety changes described above. The upstream MIT license is preserved in [LICENSE](LICENSE). Third-party notices and licenses remain in `dm/third_party/` and the relevant tool directories.

## Building

You need your own lawful game files and the tools described in the [upstream build instructions](https://github.com/seedds/nxnative#how-to-play). The `dm/games/0400A3A01EE4C000/` profile contains the game-specific tables used by the build tools. Generated game modules, RomFS data, Metal shader libraries, signing material, and the installed app are not included.

The runtime and build scripts are included so the project can be inspected and adapted. A fresh iPhone build requires generating its resources and shaders from your own input files.
