"Usage: otf2-snapshots [OPTION]... ANCHORFILE\n"
"Append snapshots to existing otf2 traces at given 'break' timestamps.\n"
"\n"
"Options:\n"
"  -n, --number <BREAKS> Number of breaks (distributed regularly)\n"
"                        if -p and -t are not set, the default for -n is 10\n"
"                        breaks.\n"
"  -p <TICK_RATE>        Create break every <TICK_RATE> ticks\n"
"                        if both, -n and -p are specified the one producing\n"
"                        more breaks wins.\n"
"      --progress        Brief mode, print progress information.\n"
"      --verbose         Verbose mode, print break timestamps, i.e. snapshot\n"
"                        informations to stdout.\n"
"  -V, --version         Print version information.\n"
"  -h, --help            Print this help information.\n"
