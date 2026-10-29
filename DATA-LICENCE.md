# Data licence and attribution

The MIT licence above covers the **code**. The bundled numbering data is
separate and carries its own terms.

## United Kingdom — `src/phonelint/_data/uk.db`

Derived from Ofcom's published telephone numbering data (the National Numbering
Scheme), used under the **Open Government Licence v3.0**.

> Contains information licensed under the Open Government Licence v3.0.
> <http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/>

Ofcom publishes allocation records for UK number ranges and updates them
roughly weekly. What is bundled here is a reshaped extract: prefix, line type,
the operator a range was allocated to, the exchange area, and whether the range
is assigned at all. No attempt is made to track porting — see the README.

Ofcom does not endorse this package and has no involvement in it.

## United States — not bundled

NANPA's allocation records are public and free to download, but NANPA publishes
no terms of use, only a blanket copyright footer. Redistributing that data
inside a package is a different act from reading it, and without written
permission it is not one this project will take on someone else's behalf.

The code is country-agnostic. If the licensing is settled the data drops in
without an API change.
