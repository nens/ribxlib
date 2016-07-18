ribxlib
==========================================

A library for parsing RIBX and RIBXA files, initially for use in the
Upload Server but without unnecessary external dependencies.

Error checking is currently not complete, there is an emphasis on the
fields that are used in the Upload Server (mostly location, ref and
inspection date fields of pipes, manholes and drains).

The RIBX parser can be run in two modes: PREINSPECTION or INSPECTION.
This influences how the RIBX is parsed.

There are two parsers: a TreeParser and an ElementParser. The
ElementParser implements specific checks for the SewerElements, i.e.,
it checks the contents inside of the ``ZB_?`` tags. The ``?`` is
variable and depends on the type of sewerage element that is being
inspected.

The following checks are currently implemented:

- ?AA (mandatory)
- ?BF (inspection date)
- For Pipes ZB_A and ZB_G:
  - ?AD and ?AF must be present (i.e., two manholes)
- ?AB (start location)
- ?AQ (ownership)
- Check for video for specific sewerage elements. If a sewerage element is
  marked as having videos, then the ?BS tag is parsed. In PREINSPECTION mode
  this may be empty, but in INSPECTION mode this must contain one video name.
- ?XD (no work done/work impossible). Also the reason is checked, we have
  the following reasons:
    - 'A': 'Voertuig/obstakel op toegang'
    - 'B': 'Straat niet toegankelijk voor het voertuig'
    - 'C': 'Groen blokkeert de toegang'
    - 'D': 'Niet aangetroffen'
    - 'E': 'Deksel vast'
    - 'Z': 'Andere reden.
  If the reason is 'Z' the '?DE' tag is parsed as the reason.
- ?XC (a new sewerage element that wasn't on the planning)
- ?ZC (observations, must be empty in PREINSPECTION mode)
