"Usage: otf2-marker [OPTION] [ARGUMENTS]... ANCHORFILE\n"
"Read or edit a marker file.\n"
"\n"
"Options:\n"
"                      Print all markers sorted by group.\n"
"      --def <GROUP> [<CATEGORY>]\n"
"                      Print all marker definitions of group <GROUP> or of\n"
"                      category <CATEGORY> from group <GROUP>.\n"
"      --defs-only     Print only marker definitions.\n"
"      --add-def <GROUP> <CATEGORY> <SEVERITY>\n"
"                      Add a new marker definition.\n"
"      --add <GROUP> <CATEGORY> <TIME> <SCOPE> <TEXT>\n"
"                      Add a marker to an existing definition.\n"
"      --remove-def <GROUP> [<CATEGORY>]\n"
"                      Remove all marker classes of group <GROUP> or only the\n"
"                      category <CATEGORY> of group <GROUP>; and all according\n"
"                      markers.\n"
"      --clear-def <GROUP> [<CATEGORY>]\n"
"                      Remove all markers of group <GROUP> or only of category\n"
"                      <CATEGORY> of group <GROUP>.\n"
"      --reset         Reset all marker.\n"
"  -V, --version       Print version information.\n"
"  -h, --help          Print this help information.\n"
"\n"
"Argument descriptions:\n"
"  <GROUP>, <CATEGORY>, <TEXT>\n"
"                      Arbitrary strings.\n"
"  <SEVERITY>          One of:\n"
"                       * NONE\n"
"                       * LOW\n"
"                       * MEDIUM\n"
"                       * HIGH\n"
"  <TIME>              One of the following formats:\n"
"                       * <TIMESTAMP>\n"
"                         A valid timestamp inside the trace range\n"
"                         'global offset' and 'global offset' + 'trace\n"
"                         length'.\n"
"                       * <TIMESTAMP>+<DURATION>\n"
"                         <TIMESTAMP> and <TIMESTAMP> + <DURATION> must be valid\n"
"                         timestamps inside the trace range 'global\n"
"                         offset' and 'global offset' + 'trace length'.\n"
"                       * <TIMESTAMP-START>-<TIMESTAMP-END>\n"
"                         Two valid timestamps inside the trace range 'global\n"
"                         offset' and 'global offset' + 'trace length', with\n"
"                         <TIMESTAMP-START> <= <TIMESTAMP-END>.\n"
"                      See the CLOCK_PROPERTIES definition with the help\n"
"                      of the 'otf2-print -G' tool.\n"
"  <SCOPE>[:<SCOPE-REF>]\n"
"                       The <SCOPE> must be one of:\n"
"                       * GLOBAL\n"
"                       * LOCATION:<LOCATION-REF>\n"
"                       * LOCATION_GROUP:<LOCATION-GROUP-REF>\n"
"                       * SYSTEM_TREE_NODE:<SYSTEM-TREE-NODE-REF>\n"
"                       * GROUP:<GROUP-REF>\n"
"                       * COMM:<COMMUNICATOR-REF>\n"
"                      <SCOPE-REF> must be a valid definition reference of\n"
"                      the specified scope. Use 'otf2-print -G' for a list of\n"
"                      defined references.\n"
"                      There is no <SCOPE-REF> for <SCOPE> 'GLOBAL'.\n"
"                      For a scope 'GROUP' the type of the referenced\n"
"                      group must be 'OTF2_GROUP_TYPE_LOCATIONS' or\n"
"                      'OTF2_GROUP_TYPE_COMM_LOCATIONS'.\n"
