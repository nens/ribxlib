Changelog of ribxlib
===================================================


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
