Changelog of ribxlib
===================================================


0.10 (unreleased)
-----------------

- Added ``bin/bin/ribxdebug`` helper tool to print the info parsed from a
  .ribx file.

- Added parsing of angle observarions ("hellinghoek") as that's needed for a
  quality checker.

  Previously, observations were only inspected for their media files. This is
  the first observation we're looking at in more depth. (Which means the
  implementation might change later on).

- Changed local development setup to use docker. Including the now-customary
  ``Jenkinsfile`` for automatic tests.

  Note: there's a small change regarding the bootstrap/buildout setup that's
  explained in the README.


0.9 (2016-12-07)
----------------

- Add parsing of inspection time (?BG).


0.8 (2016-10-21)
----------------

- Nothing changed yet.


0.7 (2016-10-21)
----------------

- Nothing changed yet.


0.6 (2016-10-13)
----------------

- Update the parser for inspection_pipes, so that it includes the
  manhole_start attribute, plus add corresponding tests and test ribx file.


0.5 (2015-09-09)
----------------

- Fix bug with setting ownership.


0.4 (2015-07-07)
----------------

- Refactored parsers.py a lot; there is now a single parser for
  all types of element.

- Return "InspectionManholes" and "CleaningManholes" separately (and
  the same for pipes). This means lizard-progress can check that the
  right type was used, which will protect against some annoying errors
  users made (uploading a file to the wrong Activity and having it
  accepted, overwriting the right data).

- Check for "XD" tags in element headers, which signify that it was not
  possible to do that part of the assigned work. The commentary is
  gatherered and returned too, for use in lizard-progress.

- Check for "XC" tags in element headers, which signify that the element
  was not part of the assigned work ("found in the field").


0.3 (2015-06-09)
----------------

- Store the value of the <EAQ> field of drains in the Drain object;
  used to signify who owns a given drain.

- It was only possible to use <N> records in observations for pipes,
  but they are used for manholes too. According to the standard, <ZC>
  records are always the same. Gave them their own object.


0.2 (2015-06-04)
----------------

- Incorporated changes for the RIBX standard 1.2 (released 27 may 2015).

  * No nl: prefixes anymore
  * Different <ZC_*> tags for different structures
  * gml:Point is now correctly capitalized


0.1 (2015-02-04)
----------------

- Initial project structure created with nensskel 1.34.

- Sufficient error checking to go live.
